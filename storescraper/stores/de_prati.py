import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class DePrati(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
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
            url_webpage = 'https://www.deprati.com.ec/search?q=LG'
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = \
                json.loads(
                    soup.find('div', {'id': 'vueApp'})['searchpagedata'])[
                    'results']
            if not product_containers:
                logging.warning('Empty category')
                break
            for container in product_containers:
                product_url = container['url']
                product_urls.append('https://www.deprati.com.ec' + product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_json = json.loads(
            soup.find('input', {'name': 'producthidden'})['value'])
        name = product_json['name']
        sku = product_json['code']
        stock = -1
        price = Decimal(
            product_json['price']['formattedValue'].replace('$', '').replace(
                '.', '').replace(',', '.'))
        picture_urls = [product_json['images'][0]['url']]
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
            'USD',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
