import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, NOTEBOOK, ALL_IN_ONE, TABLET, \
    HEADPHONES, WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Reuse(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            NOTEBOOK,
            ALL_IN_ONE,
            TABLET,
            HEADPHONES,
            WEARABLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['celulares', CELL],
            ['computadores/tipo-de-producto_notebook', NOTEBOOK],
            ['computadores/tipo-de-producto_chromebook', NOTEBOOK],
            ['computadores/tipo-de-producto_imac', ALL_IN_ONE],
            ['tablets-ipad', TABLET],
            ['accesorios-1/audifonos', HEADPHONES],
            ['accesorios-1/watch', WEARABLE]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.reuse.cl/collections/' \
                              '{}?page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'productgrid--item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://www.reuse.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_json = json.loads(
            soup.find('script', {'data-section-id': 'static-product'}).text)[
            'product']
        description = html_to_markdown(product_json['description'])

        products = []
        for variant in product_json['variants']:
            if not variant['inventory_management']:
                continue

            name = variant['name']
            sku = variant['sku']
            key = str(variant['id'])
            stock = -1 if variant['available'] else 0
            price = Decimal(variant['price'] / 100)
            picture_urls = ['https:' + tag.split('?v')[0] for tag in
                            product_json['images']]
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
                picture_urls=picture_urls,
                condition='https://schema.org/RefurbishedCondition',
                description=description
            )
            products.append(p)

        return products
