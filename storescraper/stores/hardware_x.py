import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import KEYBOARD, MONITOR, HEADPHONES, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class HardwareX(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR,
            HEADPHONES,
            MOUSE,
            KEYBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['monitores-gamer-esports', MONITOR],
            ['audifonos-headset-gamer-esports', HEADPHONES],
            ['mouse-gamer-esports', MOUSE],
            ['teclados-gamer-esports', KEYBOARD],
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
                url_webpage = 'https://www.hardwarex.cl/{}/?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_container = soup.find('div', 'main-products')

                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                containers = product_container.findAll('div', 'product-layout')
                for container in containers:
                    product_url = container.find('a', 'product-img')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        key = soup.find('input', {'id': 'product-id'})['value']
        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        name = json_data['name']
        description = json_data['description']
        price = Decimal(json_data['offers']['price'])

        max_input = soup.find('li', 'product-stock in-stock')
        if max_input:
            stock = -1
        else:
            stock = 0

        pictures_urls = []
        image_containers = soup.find('div', 'product-image')
        for i in image_containers.findAll('img'):
            pictures_urls.append(i['src'])

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
            sku=key,
            picture_urls=pictures_urls,
            description=description
        )
        return [p]
