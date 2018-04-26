import html
import json

import re
from decimal import Decimal


from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, check_ean13, \
    session_with_proxy


class Americanas(Store):
    preferred_discover_urls_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'SolidStateDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['475413', 'ExternalStorageDrive'],
            ['475433', 'SolidStateDrive'],
            ['266416', 'MemoryCard'],
            # ['263648', 'MemoryCard'],
            ['475414', 'UsbFlashDrive'],
        ]

        product_urls = []
        step = 90
        session = session_with_proxy(extra_args)

        sortings = [
            'bestSellers',
            'lowerPrice',
            'biggerPrice',
            'bestRated',
        ]

        for category_id, local_category in url_extensions:
            if local_category != category:
                continue

            for sorting in sortings:
                offset = 0

                while True:
                    if offset > 480:
                        offset = 480

                    category_url = \
                        'https://mystique-v1-americanas.b2w.io/mystique/' \
                        'search?offset={}&sortBy={}&source=omega&' \
                        'filter=%7B%22id%22%3A%22category.id%22%2C%22value' \
                        '%22%3A%22{}%22%2C%22fixed%22%3Atrue%7D' \
                        ''.format(offset, sorting, category_id)

                    print(category_url)

                    category_page = json.loads(session.get(category_url).text)

                    if 'products' not in category_page or \
                            not category_page['products']:
                        if offset == 0:
                            raise Exception('Empty category: ' + category_id)
                        break

                    for product in category_page['products']:
                        product_url = 'https://www.americanas.com.br/' \
                                      'produto/{}'.format(product['id'])
                        if product_url not in product_urls:
                            product_urls.append(product_url)

                    if offset == 480:
                        break

                    offset += step

        return list(set(product_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        response = session.get(url)

        if response.url != url:
            return []

        page_source = response.text

        main_page_json = re.search(r'window.__PRELOADED_STATE__ = (.+);',
                                   page_source)
        if not main_page_json:
            return []

        main_page_json = json.loads(main_page_json.groups()[0])

        product_json = \
            main_page_json['entities']['products']['entities']['products']
        eans_json = main_page_json['entities']['skus']['entities']['skus']
        pricing_json = main_page_json['entities']['offers']

        sizes = ['extraLarge', 'large', 'big', 'medium']

        description = html_to_markdown(html.unescape(
            main_page_json['description']['content']))

        products = []
        for page_id, page_json in product_json.items():
            name = page_json['name']

            picture_urls = []

            for image_json in page_json['images']:
                for size in sizes:
                    if size in image_json:
                        picture_url = image_json[size]
                        picture_urls.append(picture_url)
                        break

            if pricing_json[page_id]:
                normal_price = Decimal(
                    str(pricing_json[page_id][0]['salesPrice']))
                offer_price = normal_price
                stock = -1
            else:
                normal_price = Decimal(0)
                offer_price = Decimal(0)
                stock = 0

            for sku in page_json['skus']:
                if 'eans' in eans_json[sku]:
                    ean = eans_json[sku]['eans'][0]
                    while len(ean) < 13:
                        ean = '0' + ean
                    if not check_ean13(ean):
                        ean = None

                    if ean and ean == '0000000000000':
                        ean = None
                else:
                    ean = None

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
                    'BRL',
                    sku=sku,
                    ean=ean,
                    description=description,
                    picture_urls=picture_urls
                )

                products.append(p)

        return products
