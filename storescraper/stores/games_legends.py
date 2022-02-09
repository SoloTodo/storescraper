import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import RAM, PROCESSOR, MOUSE, SOLID_STATE_DRIVE, \
    MONITOR, KEYBOARD, HEADPHONES, MOTHERBOARD, POWER_SUPPLY, CELL, \
    VIDEO_CARD, COMPUTER_CASE, GAMING_CHAIR, VIDEO_GAME_CONSOLE, MICROPHONE, \
    GAMING_DESK
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
            MICROPHONE,
            GAMING_DESK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extension = [
            ['gabinetes', COMPUTER_CASE],
            ['tarjetas-de-video', VIDEO_CARD],
            ['audifonos', HEADPHONES],
            ['teclados', KEYBOARD],
            ['mouse', MOUSE],
            ['discos-internos-y-externos', SOLID_STATE_DRIVE],
            ['monitores-proyectores', MONITOR],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['sillasgamer', GAMING_CHAIR],
            ['zona-xbox', VIDEO_GAME_CONSOLE],
            ['playstation', VIDEO_GAME_CONSOLE],
            ['playstation5', VIDEO_GAME_CONSOLE],
            ['nintendo', VIDEO_GAME_CONSOLE],
            ['consolas', VIDEO_GAME_CONSOLE],
            ['memorias-ram', RAM],
            ['procesadores', PROCESSOR],
            ['placasmadres', MOTHERBOARD],
            # ['telefonos-moviles', CELL],
            ['microfonos', MICROPHONE],
            ['escritorios', GAMING_DESK]
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
                product_containers = soup.find('div',
                                               'row '
                                               'product-list mx-md-n3 mx-n2')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                product_containers = product_containers.findAll(
                    'div', 'col-lg-3')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
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

        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)
        name = json_data['name']
        key = soup.find('form', 'product-form')['action'].split('/')[-1]

        part_number_match = re.search('"productID": "(.+)"', response.text)
        if part_number_match:
            part_number = part_number_match.groups()[0]
        else:
            part_number = None

        sku = json_data.get('sku', None)

        if 'VENTA' in name.upper():
            # Preventa, skip
            stock = 0
        elif json_data['offers']['availability'] == \
                'http://schema.org/OutOfStock':
            stock = 0
        elif soup.find('span', 'product-form-stock'):
            stock = int(soup.find('span', 'product-form-stock').text)
        else:
            stock = -1

        price = Decimal(remove_words(
            soup.find('span', 'product-form_price').text))
        picture_containers = soup.find('div', 'product-images')

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
            key,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            part_number=part_number
        )
        return [p]
