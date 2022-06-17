from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup

from storescraper.categories import MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Campcom(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != MONITOR:
            return []
        url_extension = 'https://campcom.cl/shop'

        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('Page overflow: ' + url_extension)
            url_webpage = '{}/page/{}/'.format(url_extension, page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('li', 'product')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('link', {'rel': 'shortlink'})[
            'href'].split('=')[-1]
        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        if '@graph' not in json_data:
            return []

        json_data = json_data['@graph'][1]

        name = json_data['name']
        sku = str(json_data['sku'])
        offer = json_data['offers'][0]
        if 'price' in offer:
            price = Decimal(offer['price'])
        else:
            price = Decimal(offer['lowPrice'])
        stock_span = soup.find('span', 'stock in-stock')
        stock = -1
        if stock_span:
            stock = int(stock_span.text.split('disp')[0].strip())

        picture_urls = []
        picture_container = soup.find(
            'figure', 'woocommerce-product-gallery__wrapper')
        for a in picture_container.findAll('a'):
            if a['href'] != "":
                picture_urls.append(a['href'])

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
            picture_urls=picture_urls
        )

        return [p]
