import html
import json
import logging
import urllib

import demjson
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MercadoLibreChile(Store):
    @classmethod
    def categories(cls):
        categories = set()
        stores_paths = cls._category_paths().values()
        for store_paths in stores_paths:
            for store_path in store_paths:
                categories.add(store_path[1])
        return list(categories)

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        for store_extension, store_paths in cls._category_paths().items():
            for category_path, local_category in store_paths:
                if local_category != category:
                    continue

                category_url = 'https://listado.mercadolibre.cl/{}/' \
                               '{}'.format(category_path, store_extension)
                response = session.get(category_url)

                if response.url != category_url:
                    logging.warning('Invalid and/or empty category: ' +
                                    response.url)
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                title_tag = soup.find('title')

                if not title_tag or 'oficial' not in title_tag.text.lower():
                    logging.warning('Non official store: ' + response.url)
                    continue

                if soup.find('div', 'zrp-offical-message'):
                    raise Exception('Invalid category: ' + category_url)

                containers = soup.findAll('li', 'results-item')

                if not containers:
                    containers = soup.findAll('li', 'ui-search-layout__item')

                if not containers:
                    logging.warning('Empty category: ' + category_url)

                for container in containers:
                    product_url = container.find('a')['href'].split(
                        '?')[0].split('#')[0]
                    product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        new_mode_data = re.search(
            r'window.__PRELOADED_STATE__ =([\S\s]+?);\n', page_source)

        if new_mode_data:
            data = json.loads(new_mode_data.groups()[0])
            if 'component_id' in data['initialState']['components'][
                    'variations']:
                return cls.retrieve_type2_products(session, url, soup,
                                                   category, data)
            else:
                return cls.retrieve_type3_products(data, session, category)
        else:
            return cls.retrieve_type1_products(page_source, url, soup, category)

    @classmethod
    def retrieve_type3_products(cls, data, session, category):
        variations = set()

        for picker in data['initialState']['components']['variations'][
                'pickers']:
            for product in picker['products']:
                variations.add(product['id'])

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
            for variation in picker['products']:
                color_name = variation['label']['text']
                name = '{} ({})'.format(base_name, color_name)
                color_id = variation['attribute_id']

                variation_url = 'https://articulo.mercadolibre.cl/' \
                                'noindex/variation/choose?itemId={}&' \
                                'attribute={}%7C{}' \
                                ''.format(sku,
                                          urllib.parse.quote(picker['id']),
                                          urllib.parse.quote(color_id))
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
            '_Tienda_acer': [
                ('computacion/notebooks', 'Notebook'),
                ('almacenamiento', 'ExternalStorageDrive'),
                ('tablets-accesorios', 'Tablet'),
                ('monitores-accesorios', 'Monitor'),
            ],
            '_Tienda_cintegral': [
                ('notebooks-accesorios', 'Notebook'),
                ('pc-escritorio', 'AllInOne'),
                ('almacenamiento', 'SolidStateDrive'),
            ],
            '_Tienda_corsair': [
                ('notebooks-accesorios', 'CpuCooler'),
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('componentes-pc', 'PowerSupply'),
            ],
            '_Tienda_cougar': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('webcams-audio-pc', 'Headphones'),
                ('electronica', 'Headphones'),
            ],
            '_Tienda_hp': [
                ('computacion/notebooks', 'Notebook'),
                ('pc-escritorio', 'AllInOne'),
                ('computacion/impresoras/impresoras', 'Printer'),
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('almacenamiento', 'AllInOne'),
                ('monitores-accesorios', 'Monitor'),
            ],
            '_Tienda_huawei': [
                ('celulares-telefonia/celulares', 'Cell'),
                ('smartwatches-accesorios', 'Wearable'),
                ('notebooks-accesorios', 'Notebook'),
                ('tablets-accesorios', 'Tablet'),
                ('audio-audifonos', 'Headphones'),
                ('electronica/audio-hogar/parlantes-subwoofers',
                 'Headphones'),
            ],
            '_Tienda_hyperx': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('webcams-audio-pc', 'Headphones'),
            ],
            '_Tienda_lenovo': [
                ('pc-escritorio-all-in-one', 'AllInOne'),
            ],
            '_Tienda_logitech': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('mouses-teclados-controles-kits-mouse-teclado',
                 'KeyboardMouseCombo'),
                ('webcams-audio-pc', 'StereoSystem'),
            ],
            '_Tienda_logitech-g': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('webcams-audio-pc-audifonos', 'Headphones'),
                ('electronica', 'Headphones'),
                ('webcams-audio-pc-parlantes', 'StereoSystem'),
            ],
            '_Tienda_marvo': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('webcams-audio-pc-audifonos', 'Headphones'),
                ('webcams-audio-pc-parlantes', 'StereoSystem'),
            ],
            '_Tienda_ozone': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('webcams-audio-pc', 'Headphones'),
                ('videojuegos', 'Headphones'),
            ],
            '_Tienda_pc-factory_OfficialStoreId_810': [
                ('celulares-telefonia', 'Cell'),
                ('computacion', 'Notebook'),
            ],
            '_Tienda_primus': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
            ],
            '_Tienda_razer': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('webcams-audio-pc', 'Headphones'),
            ],
            '_Tienda_redragon': [
                ('mouses-teclados-controles', 'Keyboard'),
            ],
            '_Tienda_seagate': [
                ('almacenamiento-discos-accesorios-duros-ssds/externo',
                 'ExternalStorageDrive'),
                ('almacenamiento-discos-accesorios-duros-ssds/interno',
                 'StorageDrive'),
            ],
            '_Tienda_trust': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
            ],
            '_Tienda_western-digital': [
                ('almacenamiento-discos-duros-removibles-accesorios',
                 'SolidStateDrive'),
                ('almacenamiento-discos-accesorios-duros-ssds/externo',
                 'ExternalStorageDrive'),
                ('almacenamiento-discos-accesorios-duros-ssds/interno',
                 'StorageDrive'),
            ],
            '_Tienda_xpg': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('webcams-audio-pc', 'Headphones'),
            ],
            '_Tienda_xtech': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('componentes-pc', 'PowerSupply'),
                ('audio-audifonos', 'Headphones'),
            ],
            '_Tienda_blu': [
                ('celulares-telefonia/celulares', 'Cell'),
            ],
            '_Tienda_kingston': [
                ('celulares-telefonia', 'MemoryCard'),
                ('almacenamiento-discos-accesorios', 'SolidStateDrive'),
                ('almacenamiento-pen-drives', 'UsbFlashDrive'),
            ],
            '_Tienda_motorola': [
                ('audio', 'Headphones'),
                ('celulares-telefonia/celulares', 'Cell'),
                ('celulares-telefonia/accesorios-celulares', 'StereoSystem'),
            ],
            '_Tienda_nokia': [
                ('celulares-telefonia/celulares', 'Cell'),
            ],
            '_Tienda_daewoo': [
                ('refrigeracion', 'Refrigerator'),
                ('lavado-y-secado-de-ropa', 'WashingMachine'),
            ],
            '_Tienda_xiaomi': [
                ('celulares-telefonia/celulares', 'Cell'),
                ('smartwatches-accesorios-smartwatch', 'Wearable'),
                ('audio', 'Headphones'),
            ]
        }
