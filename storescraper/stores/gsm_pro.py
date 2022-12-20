import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class GsmPro(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            HEADPHONES,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['telefonos', CELL],
            ['accesorios', HEADPHONES],
            ['mundo-gamer', CELL],
            ['bajo-pedido', CELL],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.gsmpro.cl/collections/{}'\
                              '?page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                collection = soup.find('div', 'product-list--collection')
                product_containers = collection.findAll('div', 'product-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = \
                        container.findAll(
                            'button', 'product-item__action-button'
                        )[-1]['data-product-url']
                    product_urls.append(
                        'https://www.gsmpro.cl{}'.format(product_url))
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        product_data = json.loads(soup.find(
            'script', {
                'type': 'application/json',
                'data-product-json': True
            }).text)['product']

        description = html_to_markdown(product_data['description'])
        picture_urls = ['https:' + i for i in product_data['images']]

        products = []
        for variant in product_data['variants']:
            key = str(variant['id'])
            name = variant['name']
            sku = variant['sku']
            price = (Decimal(variant['price']) / Decimal(100)).quantize(0)

            if variant['available']:
                stock = -1
            else:
                stock = 0

            variant_url = '{}?variant={}'.format(url, key)

            p = Product(
                name,
                cls.__name__,
                category,
                variant_url,
                url,
                key,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                picture_urls=picture_urls,
                description=description,
            )
            products.append(p)

        return products
