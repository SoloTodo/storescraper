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
        url_extensions = [
            ['355', GROCERIES]
        ]

        session = session_with_proxy(extra_args)
        products_urls = []
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
                    products_urls.append(
                        'https://www.unimarc.cl/product/'
                        + item['detailUrl'])
                page += 1

        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        linkText = url.split('https://www.unimarc.cl/')[-1]
        api_url = 'https://www.unimarc.cl/_next/data/EPXLTQZVv8e9C2NXIi9vU/' \
            '{}.json'.format(linkText)

        session = session_with_proxy(extra_args)
        response = session.get(api_url)

        json_data = json.loads(response.text)['pageProps']['product']

        if 'data' not in json_data:
            return []
        json_data = json_data['data']

        key = json_data['productId']
        name = json_data['brand'] + ' - ' + json_data['name']
        sku = json_data['refId']
        description = json_data['description']

        ean = json_data.get('ean', None)
        if not check_ean13(ean):
            ean = None

        picture_urls = json_data['images']

        seller = json_data['sellers'][0]
        price = Decimal(seller['price'])
        if seller['availableQuantity']:
            stock = int(seller['availableQuantity'])
        else:
            stock = 0

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
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

        return [p]
