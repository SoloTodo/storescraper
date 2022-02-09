import re
import json

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import NOTEBOOK, TABLET, PRINTER, CELL, \
    WEARABLE, TELEVISION, MOUSE, VIDEO_GAME_CONSOLE, REFRIGERATOR, \
    WASHING_MACHINE, STEREO_SYSTEM, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


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
        ]

        session = session_with_proxy(extra_args)
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            category_url = '{}/api/product-search/by-category-slug?' \
                           'slug={}&sort=recommended_web&perPage=1000' \
                           '&channel=Regular_Delivery_RM_4'\
                .format(url_base, category_path)

            print(category_url)

            data = json.loads(session.get(category_url).text)['results']

            for idx, product_data in enumerate(data):
                product_url = '{}/{}/p/'.format(url_base, product_data['slug'])

                product_entries[product_url].append({
                    'category_weight': category_weight,
                    'section_name': section_name,
                    'value': idx + 1
                })

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
        data_options = soup.findAll('script', {'type': 'application/ld+json'})
        data = None
        for d in data_options:
            data = json.loads(d.text)
            if data['@type'] == "Product":
                break

        if not data or data['@type'] != "Product":
            return []

        name = data['name']
        sku = data['sku']

        if data['offers']['availability'] == "https://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        special_price = soup.find('span', 'cmrPrice')
        data_price = None

        if 'price' in data['offers']:
            data_price = data['offers']['price']
        elif 'lowPrice' in data['offers']:
            data_price = data['offers']['lowPrice']
        else:
            raise Exception('No data price')

        if special_price:
            offer_price = Decimal(
                special_price.text.replace('$', '').replace('.', '')
                .replace('UN', '').strip())
            normal_price = Decimal(data_price)
        else:
            offer_price = Decimal(data_price)
            normal_price = offer_price

        if offer_price > normal_price:
            offer_price = normal_price

        description = html_to_markdown(str(soup.find('div', 'react-tabs')))

        picture_containers = [b.find('img') for b in soup.findAll(
            'button', 'product-gallery-thumbnails-item')]
        picture_urls = [i['src'] for i in picture_containers]
        picture_urls = [p for p in picture_urls if 'placeholder' not in p]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
