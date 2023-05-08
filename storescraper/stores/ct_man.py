import json
import logging
from decimal import Decimal

import demjson
from bs4 import BeautifulSoup

from storescraper.categories import PRINTER, KEYBOARD, HEADPHONES, \
    GAMING_CHAIR, COMPUTER_CASE, RAM, POWER_SUPPLY, PROCESSOR, MOTHERBOARD, \
    VIDEO_CARD, EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, MONITOR, \
    KEYBOARD_MOUSE_COMBO, NOTEBOOK, SOLID_STATE_DRIVE, ALL_IN_ONE, \
    TELEVISION, CELL, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy, \
    remove_words


class CtMan(Store):
    @classmethod
    def categories(cls):
        return [
            PRINTER, KEYBOARD, HEADPHONES, GAMING_CHAIR, COMPUTER_CASE, RAM,
            POWER_SUPPLY, PROCESSOR, MOTHERBOARD, VIDEO_CARD,
            EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, MONITOR,
            KEYBOARD_MOUSE_COMBO, NOTEBOOK, SOLID_STATE_DRIVE, ALL_IN_ONE,
            TELEVISION, CELL, VIDEO_GAME_CONSOLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebooks/types/notebooks', NOTEBOOK],
            ['notebooks/types/memorias-ram-para-laptops', RAM],
            ['notebooks/types/memorias-ram', RAM],
            ['pc-escritorio/types/all-in-one', ALL_IN_ONE],
            ['pc-escritorio/types/gabinetes', COMPUTER_CASE],
            ['pc-escritorio/types/memorias-ram', RAM],
            ['perifericos-de-pc/types/impresoras', PRINTER],
            ['perifericos-de-pc/types/kits-de-mouse-y-teclado',
             KEYBOARD_MOUSE_COMBO],
            ['perifericos-de-pc/types/teclados-fisicos', KEYBOARD],
            ['repuestos-y-componentes/types/fuentes-de-poder', POWER_SUPPLY],
            ['repuestos-y-componentes/types/tarjetas-de-video', VIDEO_CARD],
            ['repuestos-y-componentes/types/procesadores', PROCESSOR],
            ['repuestos-y-componentes/types/placas-madre', MOTHERBOARD],
            ['repuestos-y-componentes/types/packs', PROCESSOR],
            ['almacenamiento/types/discos-duros-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento/types/discos-duros-y-ssds', SOLID_STATE_DRIVE],
            ['almacenamiento/types/pen-drives', USB_FLASH_DRIVE],
            ['almacenamiento/types/monitores', MONITOR],
            ['monitores/types/monitores', MONITOR],
            ['monitores/types/televisores', TELEVISION],
            ['electronica-audio-y-video/types/audifonos', HEADPHONES],
            ['celulares-y-telefonia/types/celulares-y-smartphones', CELL],
            ['gaming/types/audifonos', HEADPHONES],
            ['gaming/types/fuentes-de-alimentacion', POWER_SUPPLY],
            ['gaming/types/sillas-gamer', GAMING_CHAIR],
            ['gaming/types/gabinetes', COMPUTER_CASE],
            ['gaming/types/discos-duros-y-ssds', SOLID_STATE_DRIVE],
            ['gaming/types/memorias-ram', RAM],
            ['gaming/types/placas-madre', MOTHERBOARD],
            ['gaming/types/monitores', MONITOR],
            ['gaming/types/notebooks', NOTEBOOK],
            ['gaming/types/procesadores', PROCESSOR],
            ['gaming/types/memorias-ram-para-laptops', RAM],
            ['gaming/types/fuentes-de-poder', POWER_SUPPLY],
            ['gaming/types/tarjetas-de-video', VIDEO_CARD],
            ['gaming/types/kits-de-mouse-y-teclado', KEYBOARD_MOUSE_COMBO],
            ['gaming/types/consolas-de-videojuegos', VIDEO_GAME_CONSOLE],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 25:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.ctman.cl/collections/{}/' \
                              '{}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product-item')
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
        key_tag = soup.find('div', 'title-description').find('input', {'name': 'cart_item[variant_id]'})

        if not key_tag:
            return []

        key = key_tag['value']
        json_data = demjson.decode(
            soup.find('script', {'type': 'application/ld+json'}).text)
        name = json_data['name']
        sku = soup.find('p', 'product-sku').text.split(':')[1].strip()
        description = json_data['description']
        price_key = 'lowPrice' if 'lowPrice' in json_data['offers'] \
            else 'price'
        price = Decimal(remove_words(json_data['offers'][price_key]))
        stock_text = soup.find('p', 'units-in-stock').text.strip()

        if stock_text == 'Producto agotado':
            stock = 0
        else:
            stock = int(stock_text.split(':')[1])

        picture_urls = [json_data['image']]
        part_number_tag = soup.find('p', 'part-number')
        if part_number_tag:
            part_number = soup.find('p', 'part-number').contents[1].strip()
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
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number
        )
        return [p]
