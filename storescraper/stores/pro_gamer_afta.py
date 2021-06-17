import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MEMORY_CARD, HEADPHONES, CELL, \
    VIDEO_GAME_CONSOLE, STEREO_SYSTEM, KEYBOARD, POWER_SUPPLY, COMPUTER_CASE, \
    MOTHERBOARD, MONITOR, MOUSE, GAMING_CHAIR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class ProGamerAfta(Store):
    @classmethod
    def categories(cls):
        return [
            MEMORY_CARD,
            HEADPHONES,
            CELL,
            VIDEO_GAME_CONSOLE,
            STEREO_SYSTEM,
            KEYBOARD,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOTHERBOARD,
            MONITOR,
            MOUSE,
            GAMING_CHAIR,

        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['tecnologia-y-otros/almacenamiento-externo', MEMORY_CARD],
            ['tecnologia-y-otros/audifonos-tecnologia-y-otros', HEADPHONES],
            ['gamer/audifonos', HEADPHONES],
            ['tecnologia-y-otros/celulares', CELL],
            ['tecnologia-y-otros/consolas-de-juegos', VIDEO_GAME_CONSOLE],
            ['tecnologia-y-otros/parlantes', STEREO_SYSTEM],
            ['tecnologia-y-otros/teclados-y-mouse', KEYBOARD],
            ['gamer/teclado-y-mouse', KEYBOARD],
            ['gamer/fuentes-de-poder', POWER_SUPPLY],
            ['gamer/gabinetes', COMPUTER_CASE],
            ['gamer/hardware', MOTHERBOARD],
            ['gamer/monitor', MONITOR],
            ['gamer/mouse-gamer', MOUSE],
            ['gamer/sillas-gamer', GAMING_CHAIR],
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
                url_webpage = 'https://progamerafta.cl/product-category' \
                              '/{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'entry')

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
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        else:
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(
                remove_words(soup.find('p', 'price').text))
        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]

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
            picture_urls=picture_urls,
        )
        return [p]
