import json
import logging

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Bristol(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        if category != TELEVISION:
            return []

        page = 1
        while True:
            if page > 10:
                raise Exception('Page overflow')

            url_webpage = 'https://www.bristol.com.py/brand/5-lg' \
                '?page={}'.format(page)
            print(url_webpage)
            data = session.get(url_webpage)
            soup = BeautifulSoup(data.text, 'html.parser')
            product_containers = soup.find(
                'section', {'id': 'products'}).findAll('div', 'item')
            if not len(product_containers):
                if page == 1:
                    logging.warning('Empty category')
                break
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)

        if res.status_code == 500:
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        product_info = json.loads(
            soup.find('div', {'id': 'product-details'})['data-product'])

        product_id = str(product_info['id_product'])
        name = product_info['name']
        sku = product_info['reference']
        description = html_to_markdown(product_info['description'])
        stock = product_info['quantity']
        price = Decimal(product_info['price_amount'])
        picture_urls = [x['large']['url'] for x in product_info['images']]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            product_id,
            stock,
            price,
            price,
            'PYG',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
