import json
import urllib
from decimal import Decimal
from pydoc import html
from storescraper.categories import STORAGE_DRIVE, STEREO_SYSTEM, CELL, \
    ALL_IN_ONE, REFRIGERATOR, MOUSE, TELEVISION, PRINTER, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Computron(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            STEREO_SYSTEM,
            CELL,
            ALL_IN_ONE,
            TELEVISION,
            VIDEO_GAME_CONSOLE,
            PRINTER,
            MOUSE,
            REFRIGERATOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = {
            '1476': STORAGE_DRIVE,
            '1480': STEREO_SYSTEM,
            '1484': CELL,
            '1478': ALL_IN_ONE,
            '115': TELEVISION,
            '293': TELEVISION,
            '81767': TELEVISION,
            '82993': REFRIGERATOR,
            '1841': MOUSE,
            '1481': TELEVISION,
            '1483': PRINTER,
            '77603': TELEVISION,
            '1846': VIDEO_GAME_CONSOLE,
            '1475': TELEVISION,
            '5': TELEVISION,
            '11': TELEVISION,
            '1482': TELEVISION,
            '1486': TELEVISION,
            '1479': TELEVISION,
            '1477': TELEVISION
        }
        session = session_with_proxy(extra_args)
        product_urls = []
        response = session.get('https://api.computron.com.ec/api/categories'
                               '/all')
        store_categories = json.loads(response.text)['data']['categories']
        for store_category in store_categories:
            store_category_id = str(store_category['id'])
            local_category = category_paths.get(store_category_id, TELEVISION)

            if local_category != category:
                continue

            url = 'https://api.computron.com.ec/api/product/category' \
                  '/{}'.format(store_category_id)
            print(url)
            products_response = session.get(url, timeout=30)
            json_products = json.loads(products_response.text)

            if 'data' not in json_products:
                # Read timed out, just skip it
                continue

            for product in json_products['data']['products']:
                if product['manufacturer']['name'] == 'LG':
                    name = urllib.parse.quote(
                        product['name'].replace('/', '-'), safe='/:()-')
                    product_url = 'https://computron.com.ec/product-' \
                                  'detail/' + name + '/' + str(
                                    product['productId'])
                    product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        product_id = url.split('/')[-1]
        product_url = 'https://api.computron.com.ec/api/product/id/{}'.format(
            product_id)
        response = session.get(product_url, timeout=30).text
        product = json.loads(response)['data']['results'][0]
        name = product['name']
        part_number = product['external_code']
        sku = str(product['productId'])
        stock = product['stock']
        price = Decimal(product['price']['netPrice'])
        price = price.quantize(Decimal('0.01'))
        picture_urls = [html.escape(picture) for picture in product['images']]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'USD',
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls
        )
        return [p]
