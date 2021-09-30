import logging

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Bristol(Store):
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
                print(url_webpage)
                data = session.get(url_webpage)
                product_containers = data.json()['data']
                if not len(product_containers):
                    if page == 1:
                        logging.warning('Empty category')
                    break
                for container in product_containers:
                    product_url = container['slug']
                    product_urls.append(
                        'https://www.bristol.com.py/product/' + str(
                            product_url))
                page += 11
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)

        if res.status_code == 500:
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        product_id = soup.find(
            'meta', {'property': 'product:retailer_item_id'})['content']

        response = session.get(
            'https://bristol.opentechla.com/api/opentech/martfury/products/' +
            product_id)
        product_container = response.json()

        if not product_container['price']:
            return []

        name = product_container['name']
        stock = product_container['stock']
        price = Decimal(product_container['price'])
        picture_urls = [x['path'] for x in product_container['images']]

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
            sku=product_id,
            picture_urls=picture_urls
        )
        return [p]
