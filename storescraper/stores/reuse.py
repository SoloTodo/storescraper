import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, NOTEBOOK, ALL_IN_ONE, TABLET, \
    HEADPHONES, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Reuse(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            NOTEBOOK,
            ALL_IN_ONE,
            TABLET,
            HEADPHONES,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['celulares-1', CELL],
            ['computadores-1/tipo-de-producto_notebook', NOTEBOOK],
            ['computadores-1/tipo-de-producto_all-in-one', ALL_IN_ONE],
            ['tablets-1/iPad', TABLET],
            ['accesorios-1/audifonos', HEADPHONES],
            ['accesorios-1/pantalla', MONITOR]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.reuse.cl/collections/' \
                              '{}?page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'productgrid--item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://www.reuse.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_json = json.loads(
            soup.find('script', {'data-section-id': 'static-product'}).text)[
            'product']

        name = product_json['title']
        sku = str(product_json['variants'][0]['id'])
        stock = -1 if product_json['available'] else 0
        price = Decimal(remove_words(
            soup.find('div', 'price__current').find('span',
                                                    'money').text.strip()))
        picture_urls = ['https:' + tag.split('?v')[0] for tag in
                        product_json['images']]
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
            picture_urls=picture_urls,
            condition='https://schema.org/RefurbishedCondition'

        )
        return [p]
