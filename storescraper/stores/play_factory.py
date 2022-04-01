from decimal import Decimal
import json
import logging

from bs4 import BeautifulSoup

from storescraper.categories import CASE_FAN, GAMING_CHAIR, \
    KEYBOARD_MOUSE_COMBO, MICROPHONE, MONITOR, MOTHERBOARD, MOUSE, KEYBOARD, \
    HEADPHONES, COMPUTER_CASE, POWER_SUPPLY, PROCESSOR, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class PlayFactory(Store):

    @classmethod
    def categories(cls):
        return [
            KEYBOARD_MOUSE_COMBO,
            MOUSE,
            KEYBOARD,
            MONITOR,
            GAMING_CHAIR,
            VIDEO_GAME_CONSOLE,
            POWER_SUPPLY,
            MOTHERBOARD,
            CASE_FAN,
            COMPUTER_CASE,
            MICROPHONE,
            HEADPHONES,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['monitores', MONITOR],
            ['gaming-y-streaming/monitor-gamer', MONITOR],
            ['gaming-y-streaming/sillas-y-escritorios', GAMING_CHAIR],
            ['gaming-y-streaming/perifericos-gamer/teclados-gamer', KEYBOARD],
            ['computacion/perifericos/teclados', KEYBOARD],
            ['gaming-y-streaming/perifericos-gamer/mouse-gamer', MOUSE],
            ['computacion/perifericos/mouse', MOUSE],
            ['gaming-y-streaming/perifericos-gamer/kit-gamer',
                KEYBOARD_MOUSE_COMBO],
            ['gaming-y-streaming/consolas-y-controles', VIDEO_GAME_CONSOLE],
            ['criptomineria/fuente-de-poder', POWER_SUPPLY],
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-pc-gabinetes-soportes', COMPUTER_CASE],
            ['componentes/gabinete', COMPUTER_CASE],
            ['componentes/placa-madre', MOTHERBOARD],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/refrigeracion-y-ventilacion/ventilador-gabinete',
                CASE_FAN],
            ['gaming-y-streaming/streaming/microfonos', MICROPHONE],
            ['audio/audifonos-bluetooth', HEADPHONES],
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
                url_webpage = 'https://www.playfactory.cl/categoria-producto' \
                              '/{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                if '404!' in soup.text:
                    break
                product_containers = soup.findAll(
                    'div', 'product-inner product-item__inner')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find(
                        'a',
                        'woocommerce-LoopProduct-link ' +
                        'woocommerce-loop-product__link'
                    )['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('=')[-1]

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[1].text)['@graph'][0]
        name = json_data['name']
        price = Decimal(json_data['offers'][0]['price'])

        sku = soup.find('div', 'product-sku').text.split('SKU:')[-1]

        stock = 0
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split('disp')[0])

        picture_urls = []
        figures = soup.find('figure', 'woocommerce-product-gallery__wrapper')
        for a in figures.findAll('img'):
            picture_urls.append(a['src'])

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
        )

        return [p]
