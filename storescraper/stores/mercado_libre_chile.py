import html
import json
import logging
import urllib

import demjson
import re
from decimal import Decimal

import ipdb
from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, MONITOR, SOLID_STATE_DRIVE, \
    WEARABLE, PRINTER, MOUSE, ALL_IN_ONE, KEYBOARD_MOUSE_COMBO, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MercadoLibreChile(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        for store_extension, local_category in cls._category_paths().items():
            if local_category != category:
                continue
            print(store_extension)
            url_webpage = 'https://listado.mercadolibre.cl/{}'.format(
                store_extension)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('li', 'ui-search-layout__item')
            if not product_containers:
                logging.warning('Empty category: ' + store_extension)
                break

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        category = NOTEBOOK
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        new_mode_data = re.search(
            r'window.__PRELOADED_STATE__ =([\S\s]+?);\n', page_source)
        if new_mode_data:
            data = json.loads(new_mode_data.groups()[0])
            # import ipdb
            # ipdb.set_trace()

            for entry in data['initialState']['components'].get('head', []):
                if entry['id'] == 'item_status_message' and 'PAUSADA' in \
                        entry['body']['text'].upper():
                    return []
            key_to_categories = cls.category_paths()
            for possibly_category in data['initialState']['schema'][1][
                'itemListElement']:
                category_name = possibly_category['item']['name']
                # print(category_name)
                if category_name in key_to_categories:
                    category = key_to_categories[category_name]
                    break

            if 'component_id' in data['initialState']['components'][
                'variations']:
                return cls.retrieve_type2_products(session, url, soup,
                                                   category, data)
            else:
                return cls.retrieve_type3_products(data, session, category)
        else:
            return cls.retrieve_type1_products(
                page_source, url, soup, category)

    @classmethod
    def retrieve_type3_products(cls, data, session, category):
        print('Type3')
        variations = set()
        pickers = data['initialState']['components']['variations'].get(
            'pickers', None)

        if pickers:
            for picker in pickers:
                for product in picker['products']:
                    variations.add(product['id'])
        else:
            variations.add(data['initialState']['id'])

        products = []

        for variation in variations:
            sku = variation
            endpoint = 'https://www.mercadolibre.cl/p/api/products/' + \
                       variation
            variation_data = json.loads(session.get(endpoint).text)
            if variation_data['schema'][0]['offers']['availability'] == \
                    'https://schema.org/OutOfStock':
                # No price information in this case, so skip it
                continue

            if variation_data['components']['seller']['state'] == 'HIDDEN':
                continue

            name = variation_data['components']['header']['title']
            seller = variation_data['components']['seller']['title_value']
            url = variation_data['components']['metadata']['url_canonical']
            price = Decimal(variation_data['components']['price']['price']
                            ['value'])
            picture_template = variation_data['components']['gallery'][
                'picture_config']['template']
            picture_urls = []
            for picture in variation_data['components']['gallery']['pictures']:
                picture_urls.append(picture_template.format(id=picture['id']))

            products.append(Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                -1,
                price,
                price,
                'CLP',
                sku=sku,
                seller=seller,
                picture_urls=picture_urls,
                description='Type3'
            ))

        return products

    @classmethod
    def retrieve_type2_products(cls, session, url, soup, category, data):
        print('Type2')
        seller = data['initialState']['components']['track'][
            'analytics_event']['custom_dimensions'][
            'customDimensions']['officialStore']
        sku = data['initialState']['id']
        base_name = data['initialState']['components'][
            'short_description'][0]['title']
        price = Decimal(data['initialState']['schema'][0][
                            'offers']['price'])

        picker = None
        for x in data['initialState']['components']['short_description']:
            if x['id'] == 'variations' and 'pickers' in x:
                if len(x['pickers']) == 1:
                    picker = x['pickers'][0]
                else:
                    # I'm not sure how to handle multiple pickers
                    # https://articulo.mercadolibre.cl/MLC-547289939-
                    # samartband-huawei-band-4-pro-_JM
                    picker = None

        products = []

        if picker:
            picker_id = picker['id']
            for variation in picker['products']:
                color_name = variation['label']['text']
                name = '{} ({})'.format(base_name, color_name)
                color_id = variation['attribute_id']

                variation_url = '{}?attributes={}:{}'.format(url, picker_id,
                                                             color_id)
                res = session.get(variation_url)
                key_match = re.search(r'variation=(\d+)', res.url)

                if key_match:
                    key = key_match.groups()[0]
                    variation_url = '{}?variation={}'.format(url, key)
                else:
                    key = variation['id']

                products.append(Product(
                    name,
                    cls.__name__,
                    category,
                    variation_url,
                    url,
                    key,
                    -1,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    seller=seller,
                    description='Type2'
                ))
        else:
            picture_urls = [x['data-zoom'] for x in
                            soup.findAll('img', 'ui-pdp-image')[1::2]
                            if 'data-zoom' in x.attrs]
            products.append(Product(
                base_name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                -1,
                price,
                price,
                'CLP',
                sku=sku,
                seller=seller,
                picture_urls=picture_urls,
                description='Type2'
            ))
        return products

    @classmethod
    def retrieve_type1_products(cls, page_source, url, soup, category):
        print('Type1')
        name = soup.find('h1', 'item-title__primary ').text.strip()
        seller_tag = soup.find('p', 'title')
        seller = seller_tag.text.strip()
        variations = re.search(r'meli.Variations\(({[\S\s]+?})\);',
                               page_source)
        products = []

        if variations:
            variations_str = variations.groups()[0]
            variations_data = demjson.decode(variations_str)['model']

            for variation in variations_data:
                key = str(variation['id'])
                sku = soup.find('input', {'name': 'itemId'})['value']
                v_suffix = variation[
                    'attribute_combinations'][0]['value_name']
                v_name = name + "({})".format(v_suffix)
                v_url = url.split('?')[0] + "?variation={}".format(key)
                price = Decimal(variation['price'])
                picture_url_base = 'https://mlc-s2-p.mlstatic.com/{}-F.jpg'
                picture_urls = [picture_url_base.format(p_id)
                                for p_id in variation['picture_ids']]

                products.append(Product(
                    v_name,
                    cls.__name__,
                    category,
                    v_url,
                    url,
                    key,
                    -1,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    picture_urls=picture_urls,
                    seller=seller,
                    description='Type1'
                ))
        else:
            pictures_tag = soup.find('div', 'gallery-content')
            pictures_data = json.loads(
                html.unescape(pictures_tag['data-full-images']))
            picture_urls = [e['src'] for e in pictures_data]
            pricing_str = re.search(
                r'dataLayer = ([\S\s]+?);', page_source).groups()[0]
            pricing_data = json.loads(pricing_str)[0]
            sku = pricing_data['itemId']
            price = Decimal(pricing_data['localItemPrice'])

            products.append(Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                -1,
                price,
                price,
                'CLP',
                sku=sku,
                picture_urls=picture_urls,
                seller=seller,
                description='Type1'
            ))

        return products

    @classmethod
    def _category_paths(cls):
        return {
            '_Tienda_acer':NOTEBOOK,
            '_Tienda_hp': NOTEBOOK,

        }

    @classmethod
    def category_paths(cls):
        return {
            'MONITORES': MONITOR,
            'Discos Duros y SSDs': SOLID_STATE_DRIVE,
            'Notebooks': NOTEBOOK,
            'Smartbands': WEARABLE,
            'Impresoras': PRINTER,
            'Mouses': MOUSE,
            'All In One': ALL_IN_ONE,
            'Kits de Mouse y Teclado': KEYBOARD_MOUSE_COMBO,
            'Audífonos':HEADPHONES,


        }
