import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, CPU_COOLER, KEYBOARD, \
    VIDEO_CARD, MOUSE, HEADPHONES, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class PcFericos(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            CPU_COOLER,
            KEYBOARD,
            VIDEO_CARD,
            MOUSE,
            HEADPHONES,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['gabinetes-2', COMPUTER_CASE],
            ['disipadores', CPU_COOLER],
            ['refrigeracion-2', CPU_COOLER],
            ['teclados-1', KEYBOARD],
            ['tarjetas-de-video', VIDEO_CARD],
            ['mouse-gamer', MOUSE],
            ['headsets', HEADPHONES],
            ['ventilacion-2', CASE_FAN],
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

                url_webpage = 'https://pcfericos.cl/collections/{}?page={}' \
                    .format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('a', 'product-block-title')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['href']
                    product_urls.append('https://pcfericos.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-title').text
        json_container = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        products = []
        if soup.find('select'):
            variation_names = soup.find('select').findAll('option')
        for pos, product in enumerate(json_container['offers']):
            if len(json_container['offers']) > 2:
                var_name = name + ' - ' + variation_names[pos]['value']
            else:
                var_name = name

            stock = 0 if product['availability'] == \
                'http://schema.org/OutOfStock' else -1
            price = Decimal(product['price'])
            sku = product['url'].split('variant=')[-1]
            picture_urls = [json_container['image'][0]]
            p = Product(
                var_name,
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
            )
            products.append(p)
        return products
