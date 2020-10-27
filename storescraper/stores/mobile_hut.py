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
    STEREO_SYSTEM


class MobileHut(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            HEADPHONES,
            STEREO_SYSTEM,
            MOUSE,
            KEYBOARD,
            WEARABLE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            VIDEO_GAME_CONSOLE,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_urls = [
            ['89857884224', 'smartphones', CELL],
            ['89858244672', 'audifonos', HEADPHONES],
            # ['129582760000', 'audio-gamer', HEADPHONES],
            ['89858441280', 'parlantes', STEREO_SYSTEM],
            ['132833869888', 'mouses', MOUSE],
            ['129574076480', 'mouse-gamer', MOUSE],
            ['132834033728', 'teclados-1', KEYBOARD],
            ['133205065792', 'smartwatch', WEARABLE],
            ['132830560320', 'pendrives', USB_FLASH_DRIVE],
            ['132830593088', 'tarjetas-de-memoria', MEMORY_CARD],
            ['129583054912', 'consolas', VIDEO_GAME_CONSOLE],
            ['206952595607', 'monitores', MONITOR],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_id, category_name, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                api_url = 'https://filter-v6.globosoftware.net/filter?' \
                          'filter_id=26612&shop=mobilehutcl.myshopify.com&' \
                          'event=products&filter%5B271800%5D%5B%5D={}&page=' \
                          '{}'.format(category_id, page)
                print(api_url)

                if page > 10:
                    raise Exception('Page overflow: ' + api_url)

                products_data = json.loads(
                    session.get(api_url).text)['products']

                if not products_data:
                    if page == 1:
                        logging.warning('Empty category: ' + category_id)
                    break

                for product in products_data:
                    product_url = 'https://mobilehut.cl/collections' \
                                  '/{}/products/{}'\
                        .format(category_name, product['handle'])
                    product_urls.append(product_url)

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
            name = soup.find('h1', 'product_title').text + " ({})".format(color)
            stock = 0

            if soup.find('link', {'itemprop': 'availability'})['href'] == \
                    'http://schema.org/InStock':
                stock = -1

            price_text = soup.find('span', {'itemprop': 'price'}).text.strip()\
                .replace('$', '').replace('.', '')

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
