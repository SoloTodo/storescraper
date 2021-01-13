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
                product_containers = soup.findAll('div', 'product')
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
        print(url)
        session = session_with_proxy(extra_args)
        response_text = session.get(url).text

        variants_raw_data = re.search(
            r'var meta = ([\S\s]+?);\n', response_text).groups()[0]
        variants_data = json.loads(variants_raw_data)['product']['variants']

        products = []

        for variant in variants_data:
            variant_id = variant['id']
            sku = variant['sku']
            color = variant['public_title']

            variant_url = '{}?variant={}'.format(url, variant_id)
            variant_url_source = session.get(variant_url).text
            soup = BeautifulSoup(variant_url_source, 'html.parser')
            name = '{} ({})'.format(soup.find('h1', 'product_title').text,
                                    color)

            if soup.find('link', {'itemprop': 'availability'})['href'] == \
                    'http://schema.org/InStock':
                stock = -1
            else:
                stock = 0

            price_text = soup.find('span', {'itemprop': 'price'}).text\
                .strip().replace('$', '').replace('.', '')

            if price_text == '-':
                continue

            price = Decimal(price_text)
            image_containers = soup.findAll('div', 'product-single__photo')
            picture_urls = ['https:' + i['data-zoom']
                            for i in image_containers]

            description = html_to_markdown(
                str(soup.find('div', {'itemprop': 'description'})))

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
                picture_urls=picture_urls,
                description=description)

            products.append(p)

        return products
