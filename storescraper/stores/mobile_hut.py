import json
import logging
import re

from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import CELL, HEADPHONES, MOUSE, KEYBOARD, \
    WEARABLE, USB_FLASH_DRIVE, MEMORY_CARD, VIDEO_GAME_CONSOLE, MONITOR, \
    STEREO_SYSTEM, TABLET


class MobileHut(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            HEADPHONES,
            STEREO_SYSTEM,
            MOUSE,
            # KEYBOARD,
            WEARABLE,
            # USB_FLASH_DRIVE,
            # MEMORY_CARD,
            # VIDEO_GAME_CONSOLE,
            # MONITOR,
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
            # ['', KEYBOARD],
            # ['', USB_FLASH_DRIVE],
            # ['', MEMORY_CARD],
            # ['', VIDEO_GAME_CONSOLE],
            # ['', MONITOR],
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
                url_webpage = 'https://mobilehut.cl/collections/{}?page={}' \
                    .format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-collection')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty cagtegory: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://mobilehut.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        json_endpoint = url + '?view=get_json'
        json_data = json.loads(session.get(json_endpoint).text)
        products = []

        for variant in json_data['variants']:
            sku = str(variant['id'])
            name = variant['name']
            variant_url = '{}?variant={}'.format(url, sku)
            price = Decimal(variant['price'] / 100)

            if 'featured_media' in variant:
                picture_urls = [variant['featured_media'][
                                    'preview_image']['src']]
            else:
                picture_urls = ['https:' + x['src']
                                for x in json_data['images']]

            if variant['available']:
                stock = -1
            else:
                stock = 0

            p = Product(
                name,
                cls.__name__,
                category,
                variant_url,
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
