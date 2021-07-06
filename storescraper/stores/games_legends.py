import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import RAM, PROCESSOR, MOUSE, SOLID_STATE_DRIVE, \
    MONITOR, KEYBOARD, HEADPHONES, MOTHERBOARD, POWER_SUPPLY, CELL, \
    VIDEO_CARD, COMPUTER_CASE, GAMING_CHAIR, VIDEO_GAME_CONSOLE
from storescraper.utils import session_with_proxy, remove_words


class GamesLegends(Store):
    @classmethod
    def categories(cls):
        return [
            RAM,
            PROCESSOR,
            MOUSE,
            SOLID_STATE_DRIVE,
            MONITOR,
            KEYBOARD,
            HEADPHONES,
            MOTHERBOARD,
            POWER_SUPPLY,
            CELL,
            VIDEO_CARD,
            COMPUTER_CASE,
            GAMING_CHAIR,
            VIDEO_GAME_CONSOLE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extension = [
            ['memorias-ram', RAM],
            ['procesadores', PROCESSOR],
            ['mouse', MOUSE],
            ['discos-internos-y-externos', SOLID_STATE_DRIVE],
            ['monitores-proyectores', MONITOR],
            ['teclados', KEYBOARD],
            ['audifonos', HEADPHONES],
            ['placasmadres', MOTHERBOARD],
            ['fuentes-de-poder', POWER_SUPPLY],
            # ['telefonos-moviles', CELL],
            ['tarjetas-de-video', VIDEO_CARD],
            ['gabinetes', COMPUTER_CASE],
            ['sillasgamer', GAMING_CHAIR],
            ['nintendo', VIDEO_GAME_CONSOLE],
            ['consolas', VIDEO_GAME_CONSOLE],
            ['zona-xbox', VIDEO_GAME_CONSOLE],
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
                url_webpage = 'https://www.gameslegends.cl/en/{}?page=' \
                              '{}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find(
                    'div', 'row mb-md-5 mb-4 mx-n2').findAll(
                    'a', 'product-image')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['href']
                    product_urls.append(
                        'https://www.gameslegends.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'page-header').text
        sku_container = soup.find(
            'meta', property='og:image')['content']
        sku = re.search(r"/(\d+)/", sku_container).group(1)

        if 'VENTA' in name:
            # Preventa, skip
            stock = 0
        elif soup.find('div', 'form-group product-stock product-unavailable '
                              'visible') or soup.find(
            'div', 'form-group product-stock '
                   'product-out-stock visible'):
            stock = 0
        elif soup.find('span', 'product-form-stock'):
            stock = int(soup.find('span', 'product-form-stock').text)
        else:
            stock = -1

        price = Decimal(remove_words(
            soup.find('span', 'product-form-price form-price').text))
        picture_containers = soup.find('div', 'owl-thumbs')
        if picture_containers:
            picture_urls = [tag['src'].split('?')[0] for tag in
                            picture_containers.findAll('img')]
        else:
            picture_urls = [
                soup.find('div', 'main-product-image').find('img')[
                    'src'].split('?')[0]]
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
