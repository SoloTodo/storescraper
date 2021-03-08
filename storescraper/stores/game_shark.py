import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, VIDEO_GAME_CONSOLE, RAM, \
    POWER_SUPPLY, SOLID_STATE_DRIVE, VIDEO_CARD, MOTHERBOARD, PROCESSOR, \
    GAMING_CHAIR, CPU_COOLER, KEYBOARD, HEADPHONES, MOUSE, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class GameShark(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_GAME_CONSOLE,
            COMPUTER_CASE,
            RAM,
            POWER_SUPPLY,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            MOTHERBOARD,
            PROCESSOR,
            GAMING_CHAIR,
            CPU_COOLER,
            KEYBOARD,
            HEADPHONES,
            MOUSE,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['26-consolas', VIDEO_GAME_CONSOLE],
            ['29-consolas-x1', VIDEO_GAME_CONSOLE],
            ['46-consolas-nsw', VIDEO_GAME_CONSOLE],
            ['32-consolas-ps3', VIDEO_GAME_CONSOLE],
            ['36-consolas', VIDEO_GAME_CONSOLE],
            ['50-gabinetes', COMPUTER_CASE],
            ['64-memorias', RAM],
            ['68-fuentes-de-poder', POWER_SUPPLY],
            ['65-almacenamiento', SOLID_STATE_DRIVE],
            ['69-gpu', VIDEO_CARD],
            ['72-placa-madre', MOTHERBOARD],
            ['74-procesadores', PROCESSOR],
            ['60-sillas', GAMING_CHAIR],
            ['66-refrigeracion', CPU_COOLER],
            ['20-teclados', KEYBOARD],
            ['21-audifonos', HEADPHONES],
            ['22-mouse', MOUSE],
            ['70-monitores', MONITOR],
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
                url_webpage = 'http://www.gameshark.cl/sitio/{}?page={}' \
                    .format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('article',
                                                  'product-miniature')
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
        name = soup.find('h1', 'h1').text
        sku = soup.find('input', {'name': 'id_product'})['value']
        if soup.find('div', 'product-quantities'):
            stock = int(soup.find('div', 'product-quantities').find(
                'span').text.split()[0])
        else:
            stock = 0
        price = Decimal(remove_words(
            soup.find('div', 'current-price').find('span')['content']))
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'images-container').findAll('img')]
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
