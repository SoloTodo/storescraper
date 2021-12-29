import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import ALL_IN_ONE, NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Syd(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            ALL_IN_ONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://syd.cl'

        category_paths = [
            ['/collection/imac-m1', ALL_IN_ONE],
            ['/collection/imac', ALL_IN_ONE],
            ['/collection/macbook-pro-13-m1-de-apple', NOTEBOOK],
            ['/collection/macbook-pro-13', NOTEBOOK],
            ['/collection/macbook-pro-16', NOTEBOOK],
            ['/collection/macbook-air-m1', NOTEBOOK],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'

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
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'

        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[2].text)
        name = json_data['name']
        sku = json_data['sku']
        picture_urls = json_data['image']
        normal_price = Decimal(json_data['offers']['price'])
        offer_price = (normal_price * Decimal('0.97')).quantize(0)
        description = json_data['description']

        if json_data['offers']['availability'] == \
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
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
