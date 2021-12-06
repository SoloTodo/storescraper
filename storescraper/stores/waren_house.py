import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MOUSE, KEYBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class WarenHouse(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MOUSE,
            KEYBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accesorios-pc-gaming-audifonos', HEADPHONES],
            ['computacion/perifericos-accesorios/mouses', MOUSE],
            ['computacion/perifericos-accesorios/teclados', KEYBOARD]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 100:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.warenhouse.cl/listado/{}/' \
                              '_Desde_{}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li',
                                                  'ui-search-layout__item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in product_urls:
                        return product_urls
                    product_urls.append(product_url)
                page += 48
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        new_mode_data = re.search(
            r'window.__PRELOADED_STATE__ =([\S\s]+?);\n', page_source)
        data = json.loads(new_mode_data.groups()[0])
        for entry in data['initialState']['components'].get('head', []):
            if entry['id'] == 'item_status_message' and 'PAUSADA' in \
                    entry['body']['text'].upper():
                return []

        sku = data['initialState']['id']
        base_name = data['initialState']['components'][
            'short_description'][0]['title']
        price = Decimal(data['initialState']['schema'][0][
                            'offers']['price'])
        picture_urls = [x['data-zoom'] for x in
                        soup.findAll('img', 'ui-pdp-image')[1::2]
                        if 'data-zoom' in x.attrs]

        products = []
        pickers = data['initialState']['components']['variations']['pickers']
        if len(pickers) > 1:
            picker = pickers[1]
        else:
            picker = pickers[0]

        picker_id = picker['id']
        for variation in picker['products']:
            color_name = variation['label']['text']
            name = '{} ({})'.format(base_name, color_name)
            color_id = variation['attribute_id']

            if '?' in url:
                separator = '&'
            else:
                separator = '?'

            variation_url = '{}{}attributes={}:{}'.format(url, separator,
                                                          picker_id,
                                                          color_id)
            res = session.get(variation_url)
            key_match = re.search(r'variation=(\d+)', res.url)

            if key_match:
                key = key_match.groups()[0]
                variation_url = '{}?variation={}'.format(url, key)
            else:
                key = variation['id']

            p = Product(
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
                picture_urls=picture_urls,

            )

            products.append(p)
        return products
