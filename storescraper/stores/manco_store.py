import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, VIDEO_CARD, PROCESSOR, \
    MOTHERBOARD, RAM, SOLID_STATE_DRIVE, POWER_SUPPLY, CPU_COOLER, KEYBOARD, \
    MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class MancoStore(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            VIDEO_CARD,
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            CPU_COOLER,
            KEYBOARD,
            MOUSE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['10-gabinetes', COMPUTER_CASE],
            ['16-tarjetas-de-video', VIDEO_CARD],
            ['12-procesadores', PROCESSOR],
            ['15-placas-madre', MOTHERBOARD],
            ['13-memorias', RAM],
            ['11-almacenamiento', SOLID_STATE_DRIVE],
            ['14-fuentes-de-poder', POWER_SUPPLY],
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://mancostore.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('section',
                                               {'id': 'products'}).findAll(
                    'article')
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
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_json = json.loads(
            soup.find('div', {'id': 'product-details'})['data-product'])
        name = product_json['name']
        sku = str(product_json['id'])
        stock = product_json['quantity']
        price = Decimal(
            remove_words(product_json['price'].replace('\xa0', '')))
        picture_urls = [tag['src'] for tag in soup.find('ul', 'product-images '
                                                              'js-qv-product'
                                                              '-images'
                                                        ).findAll('img')]
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
        return [p]
