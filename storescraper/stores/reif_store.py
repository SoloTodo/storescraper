import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import NOTEBOOK, CELL, TABLET, HEADPHONES, \
    WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class ReifStore(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            CELL,
            TABLET,
            HEADPHONES,
            WEARABLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['556-iphone', CELL],
            ['558-ipad', TABLET],
            ['557-mac', NOTEBOOK],
            ['559-watch', WEARABLE],
            ['579-audifonos', HEADPHONES]
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
                url_webpage = 'https://www.reifstore.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)

                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                containers = soup.findAll('div',
                                          'product-description')

                if not containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_container = json.loads(
            soup.findAll('div', {'id': 'product-details'})[-1]['data-product']
        )
        name = json_container['name']
        sku = str(json_container['id_product'])
        part_number = json_container['reference']
        stock = json_container['quantity']
        price = Decimal(json_container['price_amount'])
        picture_urls = [tag['data-src'] for tag in
                        soup.find('div', 'images-container').findAll('img')]
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
            'CLP',
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls,
        )
        return [p]
