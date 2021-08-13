import json
import logging
from decimal import Decimal

import demjson
from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, HEADPHONES, \
    COMPUTER_CASE, RAM, PROCESSOR, VIDEO_CARD, MOTHERBOARD, GAMING_CHAIR, \
    KEYBOARD, POWER_SUPPLY, CPU_COOLER, MONITOR, MOUSE, USB_FLASH_DRIVE, \
    STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, KEYBOARD_MOUSE_COMBO
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class GWStore(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            MOTHERBOARD,
            COMPUTER_CASE,
            POWER_SUPPLY,
            RAM,
            USB_FLASH_DRIVE,
            MOUSE,
            KEYBOARD,
            HEADPHONES,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MONITOR,
            CPU_COOLER,
            GAMING_CHAIR,
            KEYBOARD_MOUSE_COMBO,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['4-procesadores', PROCESSOR],
            ['3-placas-madre', MOTHERBOARD],
            ['6-gabinetes', COMPUTER_CASE],
            ['10-fuentes-de-poder', POWER_SUPPLY],
            ['8-memorias', RAM],
            ['26-mouse', MOUSE],
            ['27-teclados', KEYBOARD],
            ['29-audifonos', HEADPHONES],
            ['30-sillas-gamer', GAMING_CHAIR],
            ['32-combos', KEYBOARD_MOUSE_COMBO],
            ['5-tarjetas-de-video', VIDEO_CARD],
            ['9-almacenamiento', SOLID_STATE_DRIVE],
            ['14-monitores', MONITOR],
            ['13-refrigeracion', CPU_COOLER],
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
                url_webpage = 'https://gwstore.cl/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
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
        json_data = json.loads(
            soup.findAll('script', {'type': 'application/ld+json'})[2]
                .text.replace('\n', ' '))
        name = json_data['name']
        key = soup.find('input', {'name': 'id_product'})['value']
        sku = json_data.get('sku', None)

        if json_data['offers']['availability'] == 'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0
        price = Decimal(json_data['offers']['price'])
        description = json_data.get('description', None)
        part_number = json_data.get('mpn', None)
        picture_urls = json_data['offers']['image']
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
            description=description,
            part_number=part_number
        )
        return [p]
