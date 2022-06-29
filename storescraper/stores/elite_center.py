import json
import logging
import re
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import HEADPHONES, SOLID_STATE_DRIVE, \
    MOUSE, KEYBOARD, CPU_COOLER, COMPUTER_CASE, \
    POWER_SUPPLY, RAM, MONITOR, MOTHERBOARD, \
    PROCESSOR, VIDEO_CARD, STEREO_SYSTEM, STORAGE_DRIVE, VIDEO_GAME_CONSOLE, \
    GAMING_CHAIR, NOTEBOOK, EXTERNAL_STORAGE_DRIVE, GAMING_DESK, MICROPHONE, \
    ALL_IN_ONE, TABLET, TELEVISION, MEMORY_CARD, USB_FLASH_DRIVE, \
    KEYBOARD_MOUSE_COMBO, UPS, PRINTER, CELL, WEARABLE
from storescraper.utils import html_to_markdown, session_with_proxy


class EliteCenter(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            STEREO_SYSTEM,
            STORAGE_DRIVE,
            MOUSE,
            KEYBOARD,
            SOLID_STATE_DRIVE,
            CPU_COOLER,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            VIDEO_GAME_CONSOLE,
            GAMING_CHAIR,
            NOTEBOOK,
            EXTERNAL_STORAGE_DRIVE,
            GAMING_DESK,
            MICROPHONE,
            ALL_IN_ONE,
            TABLET,
            TELEVISION,
            MEMORY_CARD,
            CELL,
            WEARABLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computadores/todo-en-uno', ALL_IN_ONE],
            ['computadores/portatiles', NOTEBOOK],
            ['computadores/tableta', TABLET],
            ['componentes-informaticos/cajas-gabinetes', COMPUTER_CASE],
            ['componentes-informaticos/ventiladores-y-sistemas-de-'
             'enfriamiento', CPU_COOLER],
            ['componentes-informaticos/tarjetas-madre-placas-madre',
             MOTHERBOARD],
            ['componentes-informaticos/procesadores-componentes-informaticos',
             PROCESSOR],
            ['componentes-informaticos/tarjetas-de-video-componentes-'
             'informaticos', VIDEO_CARD],
            ['almacenamiento/discos-de-estado-solido', SOLID_STATE_DRIVE],
            ['almacenamiento/discos-duros-internos', STORAGE_DRIVE],
            ['almacenamiento/discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['monitores/monitores-monitores', MONITOR],
            ['monitores/televisores', TELEVISION],
            ['memorias/tarjetas-de-memoria-flash', MEMORY_CARD],
            ['memorias/modulos-ram-genericos', RAM],
            ['memorias/modulos-ram-propietarios', RAM],
            ['memorias/unidades-flash-usb', USB_FLASH_DRIVE],
            ['audio-y-video/audifonos-total', HEADPHONES],
            ['perifericos/teclados-y-teclados-de-numeros', KEYBOARD],
            ['perifericos/combos-de-teclado-y-raton', KEYBOARD_MOUSE_COMBO],
            ['perifericos/ratones', MOUSE],
            ['audio-y-video/parlantes', STEREO_SYSTEM],
            ['proteccion-de-poder/ups-respaldo-de-energia', UPS],
            ['componentes-informaticos/fuentes-de-poder', POWER_SUPPLY],
            ['videojuegos/consolas-videojuegos', VIDEO_GAME_CONSOLE],
            ['muebles/sillas-muebles', GAMING_CHAIR],
            ['impresoras-y-escaneres/impresoras-ink-jet', PRINTER],
            ['impresoras-y-escaneres/impresoras-laser', PRINTER],
            ['impresoras-y-escaneres/impresoras-multifuncionales', PRINTER],
            ['celulares/celulares-desbloqueados', CELL],
            ['tecnologia-portatil/trackers-de-actividad', WEARABLE],
            ['tecnologia-portatil/relojes', WEARABLE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 30:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://elitecenter.cl/product-category/{}/' \
                              'page/{}/'.format(
                                  url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)

                data = response.text
                soup = BeautifulSoup(data, 'html5lib')
                product_containers = soup.findAll('div', 'product-grid-item')

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

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name'][:256]
        sku = product_data['sku']

        offer_price = Decimal(product_data['offers']['price']).quantize(0)
        normal_price = (offer_price * Decimal('1.049996')).quantize(0)

        key = soup.find(
            'a', 'add-request-quote-button button')['data-product_id']

        if soup.find('button', 'stock_alert_button'):
            stock = 0
        else:
            stock_tag = soup.find('p', 'stock')
            if stock_tag:
                stock_match = re.search(r'(\d+)', stock_tag.text)
                if stock_match:
                    stock = int(stock_match.groups()[0])
                else:
                    stock = -1
            else:
                stock = -1

        picture_urls = [tag['href'].split('?')[0] for tag in
                        soup.find(
                            'figure', 'woocommerce-product-gallery__wrapper')
                        .findAll('a')
                        if validators.url(tag['href'])
                        ]

        description_div = soup.find('div', {'id': 'tab-description'})
        if description_div:
            description = html_to_markdown(description_div.text)
        else:
            description = None
        part_number_text = soup.find(
            'div', {'data-id': '1072e30'}).text.strip()

        if part_number_text:
            part_number = part_number_text.split(': ')[1].strip()
        else:
            part_number = None

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls,
            description=description

        )
        return [p]
