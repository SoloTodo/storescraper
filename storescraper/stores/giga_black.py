from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import ALL_IN_ONE, NOTEBOOK, PRINTER, TABLET
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class GigaBlack(Store):
    @classmethod
    def categories(cls):
        return [
            TABLET,
            PRINTER,
            NOTEBOOK,
            ALL_IN_ONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['tablet', TABLET],
            ['impresoras', PRINTER],
            ['notebook', NOTEBOOK],
            ['pc-all-in-one', ALL_IN_ONE],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://gigablack.cl/collections/{}/' \
                              '?page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'grid-product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://gigablack.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(soup.find(
            'script', {'id': 'ProductJson-product-template'}).text)
        products = []

        name = json_data['title']
        description = json_data['description']
        picture_urls = ['https:' + i for i in json_data['images']]

        for variant in json_data['variants']:
            key = str(variant['id'])

            sku = variant['sku']
            if sku == "":
                sku = None

            variant_name = '{} ({})'.format(name, variant['title'])
            variant_url = '{}?variant={}'.format(url, key)

            if variant['available']:
                stock = -1
            else:
                stock = 0

            price = (Decimal(variant['price']) / Decimal(100)).quantize(0)

            p = Product(
                variant_name,
                cls.__name__,
                category,
                variant_url,
                url,
                key,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                picture_urls=picture_urls,
                description=description
            )
            products.append(p)
        return products
