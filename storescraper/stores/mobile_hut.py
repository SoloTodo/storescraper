import json
import logging
import re

from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy
from storescraper.categories import CELL, HEADPHONES, MOUSE, WEARABLE, \
    STEREO_SYSTEM, TABLET


class MobileHut(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            HEADPHONES,
            STEREO_SYSTEM,
            MOUSE,
            WEARABLE,
            TABLET
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['smartphones', CELL],
            ['audifonos', HEADPHONES],
            ['parlantes', STEREO_SYSTEM],
            ['mouses', MOUSE],
            ['tablets', TABLET],
            ['wearables', WEARABLE],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 0
            while True:
                if page > 200:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.searchanise.com/getresults?' \
                              'api_key=6p8J7s7V2j&restrictBy%5Bquantity%5D=1' \
                              '%7C&startIndex={}&collection={}' \
                    .format(page, url_extension)
                data = session.get(url_webpage)
                product_containers = data.json()['items']
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty cagtegory: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['link']
                    product_urls.append('https://mobilehut.cl' + product_url)
                page += 10
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_data = json.loads(
            re.search(r'var meta = (.+);', response.text).groups()[0])
        picture_urls = ['https:' + tag['src'] for tag in
                        soup.find('div', 'row theiaStickySidebar').findAll(
                            'img', 't4s-img-noscript')]
        products = []
        for variant in json_data['product']['variants']:
            name = variant['name']
            sku = str(variant['id'])
            price = Decimal(variant['price'] / 100)
            stock_container = soup.find('option', {'value': sku})
            if stock_container.has_attr('class') and stock_container['class'][
                    0] == 'nt_sold_out':
                stock = 0
            else:
                stock = -1
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
                'CLP',
                sku=sku,
                picture_urls=picture_urls
            )
            products.append(p)
        return products
