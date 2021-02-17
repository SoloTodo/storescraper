import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Syd(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Ram',
            'Tablet',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://syd.cl'

        category_paths = [
            ['/collection/macbook-pro-13-m1-de-apple', 'Notebook'],
            ['/collection/macbook-pro-13', 'Notebook'],
            ['/collection/macbook-pro-16', 'Notebook'],
            ['/collection/macbook-air', 'Notebook'],
            ['/collection/memorias', 'Ram'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = url_base + category_path

            response = session.get(category_url)

            if response.url != category_url:
                raise Exception('Invalid category: ' + category_url)

            soup = BeautifulSoup(response.text, 'html.parser')

            titles = soup.findAll('div', 'bs-product')

            if not titles:
                logging.warning('Empty category: ' + category_url)
                continue

            for title in titles:
                product_link = title.find('a')
                product_url = url_base + product_link['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)['@graph']
        product_data = None

        for data in json_data:
            if data['@type'] == 'Product':
                product_data = data
                break

        name = product_data['name']
        sku = product_data['sku']
        picture_urls = product_data['image']
        price = Decimal(product_data['offers']['price'])

        description = soup.find('section', 'bs-product-description')
        description = html_to_markdown(str(description))

        if product_data['offers']['availability'] == \
                'https://schema.org/InStock':
            stock = -1
        else:
            stock = 0

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
