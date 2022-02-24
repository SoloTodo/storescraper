import logging
import re
import urllib
from decimal import Decimal
import json

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class SamsungShop(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Television',
            'Refrigerator',
            'WashingMachine',
            'VacuumCleaner',
            'Headphones',
            'Wearable',
            'AirConditioner',
            'DishWasher',
            'Tablet',
            'Oven',
            'CellAccesory',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('mobile/accesorios', 'Headphones'),
            ('mobile/smartphones', 'Cell'),
            ('mobile/tablets', 'Tablet'),
            ('mobile/wearables', 'Wearable'),
            ('mobile/smartwatches', 'Wearable'),
            ('tv-y-audio/accesorios-tv', 'CellAccesory'),
            ('tv-y-audio/equipos-de-audio', 'StereoSystem'),
            ('tv-y-audio/tv', 'Television'),
            ('linea-blanca/accesorios', 'CellAccesory'),
            ('linea-blanca/soluciones-de-aire', 'AirConditioner'),
            ('linea-blanca/aspiradoras', 'VacuumCleaner'),
            ('linea-blanca/empotrados', 'Oven'),
            ('linea-blanca/lavadoras---secadoras', 'WashingMachine'),
            ('linea-blanca/microondas', 'Oven'),
            ('linea-blanca/refrigeradores', 'Refrigerator'),
            ('linea-blanca/lavavajillas', 'DishWasher'),
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 0
            page_size = 50

            while True:
                url = 'https://shop.samsung.cl/api/catalog_system/pub/' \
                      'products/search/{}?map=c,c&_from={}&_to={}'.format(
                        category_path, page * page_size,
                        (page + 1) * page_size - 1)
                print(url)
                data = session.get(url)

                json_data = json.loads(data.text)

                if not json_data:
                    if page == 0:
                        logging.warning('Empty category: ' + url)
                    break

                for entry in json_data:
                    product_urls.append(entry['link'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) ' \
            'AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.149 ' \
            'Safari/537.36'
        res = session.get(url)

        if res.status_code == 404 or urllib.parse.unquote(res.url) != url:
            return []

        soup = BeautifulSoup(res.text, 'html.parser')

        base_sku = soup.find('input', {'id': '___rc-p-id'})['value']

        endpoint = 'https://shop.samsung.cl/api/catalog_system/pub/' \
                   'products/search?sc=1&fq=productId:' + base_sku
        skus_data = json.loads(session.get(endpoint).text)[0]['items']
        products = []

        for sku_entry in skus_data:
            name = sku_entry['nameComplete']

            if 'Promoción' in sku_entry:
                name += ' + {}'.format(sku_entry['Promoción'][0])

            name = name[:250]
            sku = sku_entry['ean']
            key = sku_entry['itemId']
            stock = sku_entry['sellers'][0]['commertialOffer'][
                'AvailableQuantity']

            if not stock:
                # Unavailable products don't have a valid price, so skip them
                continue

            # Mark the "trade in" offers as unavailable because they are not
            # regular sale products with a specific price
            if 'TradeIn' in sku_entry and \
                    sku_entry['TradeIn'][0] == 'Con trade In':
                stock = 0

            price = Decimal(sku_entry['sellers'][0]['commertialOffer'][
                                'Price'])
            picture_urls = [x['imageUrl'] for x in sku_entry['images']]

            p = Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                part_number=sku,
                picture_urls=picture_urls
            )

            products.append(p)

        return products
