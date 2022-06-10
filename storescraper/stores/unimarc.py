from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import GROCERIES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13, session_with_proxy


class Unimarc(Store):
    @classmethod
    def categories(cls):
        return [
            GROCERIES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        return [category]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        url_extensions = [
            ['355', GROCERIES]
        ]

        session = session_with_proxy(extra_args)
        products = []
        for url_extension, local_categories in url_extensions:
            if category not in local_categories:
                continue

            page = 0
            while True:
                if page >= 50:
                    raise Exception('Page overflow ' + url_extension)

                url_webpage = 'https://bff-unimarc-web.unimarc.cl/bff-api/' \
                    'products/?from={}&to={}&fq=C:{}'.format(
                        page * 50, (page + 1) * 50 - 1, url_extension)
                print(url_webpage)
                data = session.get(url_webpage).text

                product_data = json.loads(data)['data']['products']

                if len(product_data) == 0:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for item in product_data:
                    product_url = 'https://www.unimarc.cl/product/' + \
                        item['detailUrl']
                    key = item['productId']
                    name = item['brand'] + ' - ' + item['name']
                    sku = item['refId']
                    ean = item.get('ean', None)
                    if not check_ean13(ean):
                        ean = None
                    description = item['description']
                    picture_urls = [i.split('?')[0] for i in item['images']]

                    seller = item['sellers'][0]
                    price = Decimal(seller['price'])
                    if seller['availableQuantity']:
                        stock = int(seller['availableQuantity'])
                    else:
                        stock = 0

                    p = Product(
                        name,
                        cls.__name__,
                        category,
                        product_url,
                        product_url,
                        key,
                        stock,
                        price,
                        price,
                        'CLP',
                        sku=sku,
                        ean=ean,
                        picture_urls=picture_urls,
                        description=description
                    )
                    products.append(p)
                page += 1

        return products
