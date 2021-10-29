import html
import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MiTiendaDamasco(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        if category != TELEVISION:
            return []

        page = 1
        while True:
            if page > 20:
                raise Exception('page overflow')

            url_webpage = 'https://www.mitiendadamasco.com/buscar/q-lg/' \
                          'qc-products/page-{}?collections=LG'.format(page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('li', {
                'data-hook': 'grid-layout-item'})
            if not product_containers:
                if page == 1:
                    logging.warning('empty category')
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_product = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        name = html.unescape(json_product['name'])
        sku = json_product['sku']
        if json_product['Offers'][
                'Availability'] == 'https://schema.org/InStock':
            stock = -1
        else:
            stock = 0
        price = Decimal(json_product['Offers']['price'])
        picture_urls = [json_product['image']['contentUrl']]
        description = json_product['description']

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
            picture_urls=picture_urls,
            description=description
        )
        return [p]
