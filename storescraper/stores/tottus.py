import logging
import re
import json

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GROCERIES, NOTEBOOK, TABLET, PRINTER, \
    CELL, WEARABLE, TELEVISION, MOUSE, VIDEO_GAME_CONSOLE, REFRIGERATOR, \
    WASHING_MACHINE, STEREO_SYSTEM, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13, session_with_proxy, \
    html_to_markdown


class Tottus(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            CELL,
            WEARABLE,
            TABLET,
            STEREO_SYSTEM,
            HEADPHONES,
            PRINTER,
            REFRIGERATOR,
            WASHING_MACHINE,
            NOTEBOOK,
            MOUSE,
            VIDEO_GAME_CONSOLE,
            GROCERIES
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        url_base = 'https://www.tottus.cl'

        category_paths = [
            ['televisores-cat070301', [TELEVISION], 'Televisores', 1],
            ['NoteBook-y-PC-cat011306', [NOTEBOOK], 'Notebook y PC', 1],
            ['tablet-cat2360034', [TABLET], 'Tablet', 1],
            ['impresoras-y-multifuncionales-cat070401', [PRINTER],
             'Impresoras y Multifuncionales', 1],
            ['accesorios-de-computacion', [MOUSE],
             'Accesorios de Computación', 1],
            ['consolas-y-videojuegos-cat070302', [VIDEO_GAME_CONSOLE],
             'Consolas y Videojuegos', 1],
            ['smartphones-cat2290023', [CELL], 'Smartphones', 1],
            ['smartwatch-cat3010050', [WEARABLE], 'Smartwatch', 1],
            ['freezer-y-refrigerador-cat070104', [REFRIGERATOR],
             'Freezer y Refrigerador', 1],
            ['lavadoras-y-secadoras-cat070106', [WASHING_MACHINE],
             'Lavadoras y Secadoras', 1],

            ['parlantes-cat070501', [STEREO_SYSTEM], 'Parlantes', 1],
            ['audifonos-cat3010062', [HEADPHONES], 'Audífonos', 1],
            ['despensa-cat0103', [GROCERIES], 'Despensa', 1]
        ]

        session = session_with_proxy(extra_args)
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 1
            while True:
                category_url = '{}/api/product-search/by-category-slug?' \
                    'slug={}&sort=recommended_web&perPage=1000' \
                    '&channel=Regular_Delivery_RM_4&page={}'\
                    .format(url_base, category_path, page)

                print(category_url)

                data = json.loads(session.get(category_url).text)['results']

                if len(data) == 0:
                    if page == 1:
                        logging.warning('Empty category: ' + category_path)
                    break

                for idx, product_data in enumerate(data):
                    product_url = '{}/{}/p/'.format(url_base,
                                                    product_data['slug'])

                    product_entries[product_url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': idx + 1
                    })

                page += 1

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = None

        for i in range(0, 10):
            response = session.get(url)
            if response.status_code == 200:
                break

        soup = BeautifulSoup(response.text, 'html5lib')

        with open('foo.json', 'w') as f:
            f.write(soup.find('script', {'id': '__NEXT_DATA__'}).text)

        template = json.loads(
            soup.find('script', {'id': '__NEXT_DATA__'}).text)
        page_props = template['props']['pageProps']

        with open('foo.json', 'w') as f:
            f.write(json.dumps(template))

        if 'data' in page_props:
            data = page_props['data']
        else:
            return []

        name = data['name']
        sku = data['sku']

        if 'ean' in data['attributes'] and \
                check_ean13(data['attributes']['ean']):
            ean = data['attributes']['ean']
        else:
            ean = None

        normal_price = Decimal(data['prices']['currentPrice'])
        if 'cmrPrice' in data['prices']:
            offer_price = Decimal(data['prices']['cmrPrice'])
        else:
            offer_price = normal_price

        description = html_to_markdown(data['description'])

        picture_urls = data['images']

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls,
            ean=ean
        )

        return [p]
