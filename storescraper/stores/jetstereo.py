import json
import logging
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy
from storescraper.categories import TELEVISION, STEREO_SYSTEM, CELL, \
    REFRIGERATOR, OVEN, WASHING_MACHINE, STOVE, CELL_ACCESORY


class Jetstereo(Store):
    base_url = 'https://www.jetstereo.com'

    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            STEREO_SYSTEM,
            CELL,
            REFRIGERATOR,
            OVEN,
            WASHING_MACHINE,
            STOVE,
            CELL_ACCESORY,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['48', STEREO_SYSTEM, ],
            ['41', TELEVISION],
            ['26', CELL],
            ['74', REFRIGERATOR],
            ['75', STOVE],
            ['76', OVEN],
            ['77', WASHING_MACHINE],
            ['63', CELL_ACCESORY]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception('Page overflow: ' + url_extension)
                url = 'https://api.jetstereo.com/manufacturers/2/' \
                      'categories/{}/products?per-page=20&page={}'.format(
                        url_extension, page)
                print(url)
                response = session.get(url)
                product_containers = json.loads(response.text)['content']

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url)
                    break

                for container in product_containers:
                    product_url = 'https://www.jetstereo.com/product/' + \
                                  container['url'].split('.com/')[-1]
                    if product_url in product_urls:
                        return product_urls
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_json = json.loads(
            soup.find('script', {'id': '__NEXT_DATA__'}).text)['props'][
            'pageProps']['product']
        name = product_json['name']
        sku = str(product_json['id'])
        part_number = product_json['sku']

        if product_json['saleStatus'] == 'AVAILABLE':
            stock = -1
        else:
            stock = 0
        price = Decimal(product_json['price']['sale'])
        picture_urls = [urllib.parse.quote(picture_url, safe='://') for
                        picture_url in
                        product_json['allImages']['full']]

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
            'HNL',
            sku=sku,
            picture_urls=picture_urls,
            part_number=part_number
        )

        return [p]
