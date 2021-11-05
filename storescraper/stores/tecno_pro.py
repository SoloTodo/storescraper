import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.banner_sections import TELEVISIONS
from storescraper.categories import VIDEO_GAME_CONSOLE, VIDEO_GAME, NOTEBOOK, \
    VIDEO_CARD, PROCESSOR, RAM, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    USB_FLASH_DRIVE, MEMORY_CARD, EXTERNAL_STORAGE_DRIVE, COMPUTER_CASE, \
    MONITOR, MOTHERBOARD, POWER_SUPPLY, KEYBOARD, MOUSE, CPU_COOLER, \
    GAMING_CHAIR, HEADPHONES, CELL, ALL_IN_ONE, TABLET, WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class TecnoPro(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_GAME_CONSOLE,
            VIDEO_GAME,
            NOTEBOOK,
            VIDEO_CARD,
            PROCESSOR,
            RAM,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            EXTERNAL_STORAGE_DRIVE,
            COMPUTER_CASE,
            MONITOR,
            MOTHERBOARD,
            POWER_SUPPLY,
            KEYBOARD,
            MOUSE,
            CPU_COOLER,
            GAMING_CHAIR,
            TELEVISIONS,
            HEADPHONES,
            CELL,
            ALL_IN_ONE,
            TABLET,
            WEARABLE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['playstation', VIDEO_GAME_CONSOLE],
            ['xbox', VIDEO_GAME_CONSOLE],
            ['nintendo', VIDEO_GAME_CONSOLE],
            ['videojuegos', VIDEO_GAME, ],
            ['notebook-y-computadores', NOTEBOOK],
            ['tarjetas-de-video', VIDEO_CARD],
            ['procesadores', PROCESSOR],
            ['memoria-ram', RAM],
            ['disco-duro', STORAGE_DRIVE],
            ['disco-ssd', SOLID_STATE_DRIVE],
            ['pendrives', USB_FLASH_DRIVE],
            ['memorias-y-pendrive', MEMORY_CARD],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['gabinetes', COMPUTER_CASE],
            ['monitores', MONITOR],
            ['placas-madres', MOTHERBOARD],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['teclados', KEYBOARD],
            ['mouses-y-teclados', MOUSE],
            ['refrigeracion-cpu', CPU_COOLER],
            ['sillas-y-mesas-gamers', GAMING_CHAIR],
            ['televisores', TELEVISIONS],
            ['audifonos', HEADPHONES],
            ['iphone-1', CELL],
            ['imac', ALL_IN_ONE],
            ['macbook', NOTEBOOK],
            ['ipad', TABLET],
            ['apple-watch', WEARABLE],
            ['audifonos-apple', HEADPHONES],
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
                url_webpage = 'https://tecnopro.cl/collections/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-card-grid')

                if not product_containers:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://tecnopro.cl'+ product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('div', 'product-detail-name').text.strip()
        sku = soup.find('span','variant-sku').text
        if soup.find('span','in-stock'):
            stock = -1
        else:
            stock = 0
        price_container = soup.find('dl','price')
        if price_container.find('div','price__sale'):
            price = Decimal(remove_words( price_container.find('div',
                            'price__sale').find('span',
                                                'price-item').text.strip()))
        else:
            price = Decimal(remove_words(price_container.find('div',
                            'price__regular').find('span',
                                                   'price-item').text.strip()))
        picture_urls = ['https:' + tag['data-src'].split('?')[0] for tag in
                        soup.find('div',
                                  'gp-product-media-wrapper').findAll('img')]

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