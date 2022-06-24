import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import KEYBOARD_MOUSE_COMBO, HEADPHONES, \
    STORAGE_DRIVE, SOLID_STATE_DRIVE, RAM, MONITOR, MOUSE, NOTEBOOK, \
    STEREO_SYSTEM, USB_FLASH_DRIVE, TABLET, KEYBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Notetop(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            RAM,
            MONITOR,
            MOUSE,
            NOTEBOOK,
            STEREO_SYSTEM,
            USB_FLASH_DRIVE,
            TABLET,
            KEYBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['auriculares', HEADPHONES],
            ['combo-mouse-y-teclado', KEYBOARD_MOUSE_COMBO],
            ['disco-hdd', STORAGE_DRIVE],
            ['disco-ssd', SOLID_STATE_DRIVE],
            ['memoria-ram', RAM],
            ['monitor', MONITOR],
            ['mouse-2', MOUSE],
            ['notebook-profesional', NOTEBOOK],
            ['parlantes', STEREO_SYSTEM],
            ['pendrive', USB_FLASH_DRIVE],
            ['tablet', TABLET],
            ['teclado', KEYBOARD]

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
                url_webpage = 'https://www.notetop.cl/search?product_types' \
                              '%5B%5D={}&page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', {'id': 'search-results'
                                                       }).findAll('li')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category; ' + url_extension)
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
        product_container = json.loads(
            soup.find('script', {'id': 'product-ld-json-data'}
                      ).text.replace('\\_', '_').replace('\\~', '~'),
            strict=False)
        name = product_container['name']
        key = product_container['productID']
        sku = product_container.get('sku', None)
        description = product_container['description']
        if product_container['offers']['offers'][0]['availability'] == \
                'http://schema.org/InStock':
            stock = int(soup.find('div', 'title-description').findAll('div',
                                                                      'marca')
                        [-1].text.strip().split('Stock:')[-1].strip())
        else:
            stock = 0
        price = Decimal(product_container['offers']['lowPrice'])
        picture_urls = [tag['src'] for tag in
                        soup.find('div', {'id': 'product-images'}).findAll(
                            'img')]
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
            picture_urls=picture_urls,
            description=description
        )
        return [p]
