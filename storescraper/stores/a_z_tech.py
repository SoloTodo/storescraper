from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import ALL_IN_ONE, CELL, COMPUTER_CASE, \
    CPU_COOLER, HEADPHONES, KEYBOARD, KEYBOARD_MOUSE_COMBO, MEMORY_CARD, \
    MICROPHONE, MONITOR, MOTHERBOARD, MOUSE, NOTEBOOK, POWER_SUPPLY, PRINTER, \
    PROCESSOR, SOLID_STATE_DRIVE, STEREO_SYSTEM, TABLET, TELEVISION, \
    USB_FLASH_DRIVE, VIDEO_CARD, VIDEO_GAME_CONSOLE, WEARABLE, RAM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy


class AZTech(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            USB_FLASH_DRIVE,
            SOLID_STATE_DRIVE,
            MEMORY_CARD,
            ALL_IN_ONE,
            KEYBOARD_MOUSE_COMBO,
            MOUSE,
            KEYBOARD,
            COMPUTER_CASE,
            TABLET,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            RAM,
            POWER_SUPPLY,
            VIDEO_CARD,
            CPU_COOLER,
            WEARABLE,
            HEADPHONES,
            TELEVISION,
            PRINTER,
            STEREO_SYSTEM,
            CELL,
            VIDEO_GAME_CONSOLE,
            MICROPHONE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebooks', NOTEBOOK],
            ['pendrive', USB_FLASH_DRIVE],
            ['discos-duros', SOLID_STATE_DRIVE],
            ['tarjeta-flash-micro-sd', MEMORY_CARD],
            ['pc-all-in-one', ALL_IN_ONE],
            ['kits', KEYBOARD_MOUSE_COMBO],
            ['mouse', MOUSE],
            ['teclados', KEYBOARD],
            ['gabinetes', COMPUTER_CASE],
            ['tablets', TABLET],
            ['monitor', MONITOR],
            ['placas-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['memorias-ram', RAM],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['tarjetas-de-video', VIDEO_CARD],
            ['refrigeracion-y-ventilacion', CPU_COOLER],
            ['macbook-pro', NOTEBOOK],
            ['macbook-air', NOTEBOOK],
            ['imac', ALL_IN_ONE],
            ['ipad-pro', TABLET],
            ['ipad-air', TABLET],
            ['ipad-10-2', TABLET],
            ['ipad-mini', TABLET],
            ['apple-watch-ultra', WEARABLE],
            ['apple-watch-series-8', WEARABLE],
            ['apple-watch-se-2-gen', WEARABLE],
            ['airpods', HEADPHONES],
            ['smart-tv', TELEVISION],
            ['impresoras-laser', PRINTER],
            ['multifuncionales', PRINTER],
            ['impresoras-de-tinta', PRINTER],
            ['parlantes', STEREO_SYSTEM],
            ['audifonos', HEADPHONES],
            ['marcas', CELL],
            ['wearables', WEARABLE],
            ['consolas', VIDEO_GAME_CONSOLE],
            ['microfonos-streamers', MICROPHONE],
            ['audifonos-gamer', HEADPHONES],
            ['mouse-gamer', MOUSE],
            ['teclados-gamer', KEYBOARD],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://onesolution.cl/collections/{}?page' \
                    '={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
                    'li', 'product')
                if not product_containers or len(product_containers) == 0:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://onesolution.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        try:
            json_data = json.loads(
                soup.findAll('script', {'type': 'application/ld+json'}
                             )[1].text)
        except Exception as e:
            json_data = None

        if json_data:
            key = json_data['productID']
            name = json_data['name']
            sku = json_data['sku']
            description = json_data['description']
            price = Decimal(remove_words(json_data['offers']['price']))

            if json_data['offers']['availability'] == \
                    'http://schema.org/InStock':
                stock = -1
            else:
                stock = 0
        else:
            product_div = soup.find('div', 'productView-price')
            key = product_div['id'].split('-')[-1]
            name = soup.find('h1', 'productView-title').text.strip()
            sku = soup.find('div', {'data-sku': True}).findAll('span')[-1].text
            description = soup.find('div', 'productView-desc').text.strip()
            price = Decimal(remove_words(
                product_div.find('span', 'price-item').text))

            if soup.find('div', {'data-inventory': True}
                         ).findAll('span')[-1].text.upper() == 'EN STOCK':
                stock = -1
            else:
                stock = 0

        picture_urls = []
        picture_container = soup.find('div', 'productView-image-wrapper')
        for i in picture_container.findAll('img'):
            picture_urls.append('https:' + i['src'])

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
            sku=key,
            part_number=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
