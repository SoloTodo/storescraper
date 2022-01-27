import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, POWER_SUPPLY, COMPUTER_CASE, \
    MONITOR, CPU_COOLER, PRINTER, MOUSE, HEADPHONES, STEREO_SYSTEM, KEYBOARD, \
    MEMORY_CARD, GAMING_CHAIR, MICROPHONE, GAMING_DESK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Gelcom(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MONITOR,
            CPU_COOLER,
            PRINTER,
            MOUSE,
            HEADPHONES,
            STEREO_SYSTEM,
            KEYBOARD,
            GAMING_CHAIR,
            MICROPHONE,
            GAMING_DESK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # AUDIO
            ['12-audifonos', HEADPHONES],
            ['20-parlantes-bluetooth', STEREO_SYSTEM],
            ['21-parlantes-karaoke', STEREO_SYSTEM],
            # COMPUTACION
            ['63-mouse', MOUSE],
            ['65-parlantes-pc', STEREO_SYSTEM],
            ['64-teclados', KEYBOARD],
            ['73-discos-duros-externo', EXTERNAL_STORAGE_DRIVE],
            ['74-discos-duros-internos', STORAGE_DRIVE],
            ['75-discos-ssd', SOLID_STATE_DRIVE],
            ['72-pendrive', USB_FLASH_DRIVE],
            ['76-tarjetas-de-memoria', MEMORY_CARD],
            ['78-impresoras', PRINTER],
            ['188-fuentes-de-poder', POWER_SUPPLY],
            ['189-gabinetes', COMPUTER_CASE],
            ['67-monitores', MONITOR],
            ['190-refrigeracion-y-ventiladores', CPU_COOLER],
            # GAMING
            ['43-audifonos-gamers', HEADPHONES],
            ['41-mouse-gamers', MOUSE],
            ['46-parlantes-gamers', STEREO_SYSTEM],
            ['42-teclados-gamers', KEYBOARD],
            ['52-sillas-gamers', GAMING_CHAIR],
            ['233-fuentes-de-poder-gamer', POWER_SUPPLY],
            ['47-gabinetes-gamers', COMPUTER_CASE],
            ['232-refrigeracion-gamer', CPU_COOLER],
            ['53-escritorios-gamers', GAMING_DESK],
            ['50-microfonos-gamers', MICROPHONE]
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

                url_webpage = 'https://www.gelcom.cl/{}?page={}'.format(
                    url_extension,
                    page)
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
        product_container = json.loads(
            soup.find('div', {'id': 'product-details'})['data-product'])
        name = product_container['name']
        sku = str(product_container['id_product'])
        stock = -1 if product_container['availability'] == 'available' else 0
        price = Decimal(product_container['price_amount'])
        picture_urls = [tag['src'] for tag in
                        soup.find('ul', 'product-images').findAll('img')]
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
