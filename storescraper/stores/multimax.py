import logging

from decimal import Decimal
import demjson
import re

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown

from storescraper.utils import check_ean13


class Multimax(Store):
    @classmethod
    def categories(cls):
        return [
            'Television'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            'Television'
        ]

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/json'
        product_urls = []

        for local_category in category_filters:
            if local_category != category:
                continue
            page = 0
            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                request_payload = {
                    "requests": [
                        {
                            "indexName": "shopify_products",
                            "params": "query=lg&page={}&"
                                      "filters=inventory_quantity%20%3E%200"
                                      .format(page)
                        }
                    ]
                }

                response = session.post(
                    'https://xzpkbvohi2-dsn.algolia.net/1/indexes/*/'
                    'queries?x-algolia-application-id=XZPKBVOHI2&'
                    'x-algolia-api-key=fc38d95d175774c9f8aa348ea65f9722',
                    json=request_payload)

                products_data = response.json()['results'][0]['hits']

                if not products_data:
                    if page == 1:
                        logging.warning('Empty category')
                    break
                for product_entry in products_data:
                    product_urls.append(
                        'https://www.multimax.net/products/' +
                        product_entry['handle'])
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
