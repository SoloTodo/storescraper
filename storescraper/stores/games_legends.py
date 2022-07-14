import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import EXTERNAL_STORAGE_DRIVE, MEMORY_CARD, \
    MOUSE, KEYBOARD, HEADPHONES, STEREO_SYSTEM, TABLET, USB_FLASH_DRIVE, \
    GAMING_CHAIR, VIDEO_GAME_CONSOLE, MICROPHONE
from storescraper.utils import session_with_proxy, remove_words


class GamesLegends(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            KEYBOARD,
            HEADPHONES,
            GAMING_CHAIR,
            VIDEO_GAME_CONSOLE,
            MICROPHONE,
            EXTERNAL_STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            STEREO_SYSTEM,
            TABLET,
            MEMORY_CARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extension = [
            ['9-consolas', VIDEO_GAME_CONSOLE],
            ['85-discos-externos', EXTERNAL_STORAGE_DRIVE],
            ['88-pendrives', USB_FLASH_DRIVE],
            ['90-tarjetas-de-memoria-', MEMORY_CARD],
            ['92-audifonos-', HEADPHONES],
            ['97-parlantes-', STEREO_SYSTEM],
            ['99-teclados-', KEYBOARD],
            ['100-audifonos-gamers-', HEADPHONES],
            ['102-teclados-gamers-', KEYBOARD],
            ['103-mouse', MOUSE],
            ['105-sillas', GAMING_CHAIR],
            ['106-microfonos-', MICROPHONE],
            ['120-tablets', TABLET],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extension:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.gameslegends.cl/{}?page=' \
                              '{}'.format(url_extension, page)
                print(url_webpage)
                res = session.get(url_webpage)

                if res.status_code == 404:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                soup = BeautifulSoup(res.text, 'html.parser')
                product_containers = soup.find('div', 'products')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                product_containers = product_containers.findAll(
                    'article', 'product-miniature')

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

        key = soup.find('input', {'id': 'product_page_product_id'})['value']
        name = soup.find('title').text.strip()
        sku = soup.find('span', {'itemprop': 'sku'}).text.replace('SKU: ', '')

        if 'disabled' in soup.find('button', 'add-to-cart').attrs:
            stock = 0
        else:
            stock = -1

        price = Decimal(soup.find('span', {'itemprop': 'price'})['content'])

        picture_urls = []
        picture_container = soup.find('div', 'swiper-wrapper')
        for i in picture_container.findAll('img'):
            picture_urls.append(i['content'])

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
            part_number=sku
        )
        return [p]
