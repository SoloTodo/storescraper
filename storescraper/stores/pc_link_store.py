import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MOUSE, KEYBOARD, \
    KEYBOARD_MOUSE_COMBO, CPU_COOLER, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, RAM, MOTHERBOARD, VIDEO_CARD, COMPUTER_CASE, \
    NOTEBOOK, MONITOR, STEREO_SYSTEM, GAMING_CHAIR, TABLET, \
    VIDEO_GAME_CONSOLE, PROCESSOR, MEMORY_CARD, USB_FLASH_DRIVE, CELL, \
    POWER_SUPPLY, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class PcLinkStore(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            CPU_COOLER,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            RAM,
            MOTHERBOARD,
            VIDEO_CARD,
            COMPUTER_CASE,
            VIDEO_GAME_CONSOLE,
            NOTEBOOK,
            MONITOR,
            STEREO_SYSTEM,
            GAMING_CHAIR,
            TABLET,
            PROCESSOR,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            CELL,
            POWER_SUPPLY,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accesorios/audifono-gamers', HEADPHONES],
            ['accesorios/mouse', MOUSE],
            ['accesorios/teclados', KEYBOARD],
            ['accesorios/kit-teclado-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['accesorios/flash-drive-usb', USB_FLASH_DRIVE],
            ['celulares', CELL],
            ['disipador/water-cooling', CPU_COOLER],
            ['componentes/fuente-de-poder', POWER_SUPPLY],
            ['componentes/disco-duro-sata', STORAGE_DRIVE],
            ['componentes/disco-duro-ssd', SOLID_STATE_DRIVE],
            ['componentes/disco-duro-externo', EXTERNAL_STORAGE_DRIVE],
            ['componentes/gabinete', COMPUTER_CASE],
            ['componentes/memoria-ram', RAM],
            ['placas-madres', MOTHERBOARD],
            ['componentes/procesador', PROCESSOR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['consolas', VIDEO_GAME_CONSOLE],
            ['notebook', NOTEBOOK],
            ['monitores', MONITOR],
            ['parlantes', STEREO_SYSTEM],
            ['sillas-gamers', GAMING_CHAIR],
            ['tablet', TABLET],
            ['accesorios/tarjetas-de-memoria', MEMORY_CARD],
            ['accesorios/pendrive', USB_FLASH_DRIVE],
            ['accesorios/microfono', MICROPHONE]
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
                url_webpage = 'https://www.pclinkstore.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'col-lg-12 col-md-12')
                if not product_containers or not product_containers.findAll(
                        'div', 'col-lg-3'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('div', 'col-lg-3'):
                    product_url = container.find('a')['href']
                    product_urls.append('https://www.pclinkstore.cl' +
                                        product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_data = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        name = product_data['name']
        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div', 'product-images').findAll('img')]

        product_data_match = re.search('var productInfo = (.+);',
                                       response.text)
        key = soup.find('form', 'product-form')['action'].split('/')[-1]
        price = Decimal(product_data['offers']['price'])

        if product_data_match:
            product_data = json.loads(product_data_match.groups()[0])

            if not product_data:
                return []

            sku = product_data[0]['variant']['sku']
            stock = 0

            for variant in product_data:
                assert str(variant['variant']['product_id']) == key
                assert variant['variant']['sku'] == sku
                stock += variant['variant']['stock']
        else:
            sku = product_data['sku']
            stock = int(soup.find('input', {'id': 'input-qty'})['max'])

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
            part_number=sku,
            picture_urls=picture_urls
        )
        return [p]
