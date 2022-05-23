import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, VIDEO_GAME_CONSOLE, RAM, \
    POWER_SUPPLY, SOLID_STATE_DRIVE, VIDEO_CARD, MOTHERBOARD, PROCESSOR, \
    GAMING_CHAIR, CPU_COOLER, KEYBOARD, HEADPHONES, MOUSE, MONITOR, \
    MEMORY_CARD, STEREO_SYSTEM, MICROPHONE
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
            STEREO_SYSTEM,
            MEMORY_CARD,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['66-consolas', VIDEO_GAME_CONSOLE],
            ['62-consolas', VIDEO_GAME_CONSOLE],
            ['79-consolas', VIDEO_GAME_CONSOLE],
            ['19-consolas', VIDEO_GAME_CONSOLE],
            ['21-tarjetas-sd', MEMORY_CARD],
            ['40-fuentes-de-poder', POWER_SUPPLY],
            ['45-video', VIDEO_CARD],
            ['46-motherboards', MOTHERBOARD],
            ['47-ram', RAM],
            ['51-procesadores', PROCESSOR],
            ['52-refrigeracion', CPU_COOLER],
            ['53-sillas', GAMING_CHAIR],
            ['49-mouse', MOUSE],
            ['54-teclados', KEYBOARD],
            ['35-audifonos', HEADPHONES],
            ['38-parlantes', STEREO_SYSTEM],
            ['29-almacenamiento', SOLID_STATE_DRIVE],
            ['41-gabinetes', COMPUTER_CASE],
            ['42-monitores', MONITOR],
            ['28-refrigeracion', CPU_COOLER],
            ['37-microfonos', MICROPHONE]
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
                url_webpage = 'http://www.gameshark.cl/{}?page={}' \
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
        product_data = json.loads(
            soup.find('div', {'id': 'product-details'})['data-product'])
        name = product_data['name']
        description = product_data['description_short']
        key = str(product_data['id'])
        sku = product_data['reference']
        stock = product_data['quantity']
        price = Decimal(product_data['price_amount'])
        picture_urls = [tag['bySize']['large_default']['url'] for tag in
                        product_data['images']]
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
