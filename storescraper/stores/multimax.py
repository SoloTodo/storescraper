import logging

from decimal import Decimal
import demjson
import re

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown

from storescraper.utils import check_ean13


class Multimax(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page >= 10:
                raise Exception('Page overflow')

            url_webpage = 'https://www.multimax.net/search?page={}&q=lg' \
                .format(page)
            print(url_webpage)

            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.find('div', 'search-results '
                                                  'column-narrow').findAll(
                'div', 'search-result search-result-product table')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category')
                break
            for container in product_containers:
                product_url = container.find(
                    'a', 'result-title')['href'].split('?')[0]
                product_urls.append(
                    'https://www.multimax.net' + product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        products = []
        json_data = demjson.decode(
            re.search(r'current: ([\s\S]*?),\n[ \t]+customerLoggedIn',
                      response.text).groups()[0])['product']

        description = html_to_markdown(json_data['description'])

        images = json_data['images']
        picture_urls = ['https:{}'.format(image.split('?')[0])
                        for image in images]

        for variant in json_data['variants']:
            name = variant['name']
            sku = variant['sku']
            barcode = variant['barcode']

            if len(barcode) == 12:
                barcode = '0' + barcode

            if not check_ean13(barcode):
                barcode = None

            # The stock may be listed as zero for available products, and no
            # active products at Multimax seem to be unavailable, so
            # assume available stok but unkwon quantity
            stock = variant['inventory_quantity'] or -1
            price = Decimal(variant['price']) / Decimal(100)

            products.append(Product(
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
                ean=barcode,
                description=description,
                picture_urls=picture_urls
            ))

        return products
