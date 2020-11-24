import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Bristol(Store):
    base_url = 'https://www.lg.com'
    country_code = 'cl'

    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            TELEVISION
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                url_webpage = 'https://bristol.opentechla.com/api/opentech' \
                              '/martfury/products?_start={}' \
                              '&perPage=12&brand=lg'.format(page)
                data = session.get(url_webpage)
                product_containers = data.json()['data']
                if not len(product_containers):
                    if page == 1:
                        logging.warning('Empty category')
                    break
                for container in product_containers:
                    product_url = container['id']
                    product_urls.append(
                        'https://www.bristol.com.py/product/' + str(
                            product_url))
                page += 11
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        product_id = url.split('/')[-1]
        session = session_with_proxy(extra_args)
        response = session.get(
            'https://bristol.opentechla.com/api/opentech/martfury/products/' +
            product_id)
        product_container = response.json()
        name = product_container['name']
        sku = str(product_id)
        stock = -1
        price = Decimal(product_container['price'])
        picture_urls = []
        if len(product_container['images']):
            picture_urls.append(product_container['images'][0]['path'])

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
            'PYG',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
