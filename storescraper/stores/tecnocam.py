import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, CASE_FAN, CELL, CPU_COOLER, \
    EXTERNAL_STORAGE_DRIVE, GAMING_CHAIR, KEYBOARD, KEYBOARD_MOUSE_COMBO, \
    MEMORY_CARD, MOTHERBOARD, MOUSE, POWER_SUPPLY, TABLET, TELEVISION, \
    VIDEO_CARD, SOLID_STATE_DRIVE, STORAGE_DRIVE, COMPUTER_CASE, PROCESSOR, \
    RAM, MONITOR, HEADPHONES, NOTEBOOK, USB_FLASH_DRIVE, STEREO_SYSTEM, \
    MICROPHONE, VIDEO_GAME_CONSOLE, PRINTER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Tecnocam(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            PROCESSOR,
            CPU_COOLER,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            VIDEO_CARD,
            CASE_FAN,
            GAMING_CHAIR,
            KEYBOARD_MOUSE_COMBO,
            MOUSE,
            KEYBOARD,
            HEADPHONES,
            MICROPHONE,
            MONITOR,
            STEREO_SYSTEM,
            TELEVISION,
            CELL,
            ALL_IN_ONE,
            VIDEO_GAME_CONSOLE,
            NOTEBOOK,
            PRINTER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento/disco-externo', EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento/disco-hdd', STORAGE_DRIVE],
            ['almacenamiento/disco-ssd', SOLID_STATE_DRIVE],
            ['almacenamiento/pendrive', USB_FLASH_DRIVE],
            ['almacenamiento/tarjeta-de-memoria', MEMORY_CARD],
            ['componentes-de-pc/cpu-amd', PROCESSOR],
            ['componentes-de-pc/cpu-intel', PROCESSOR],
            ['componentes-de-pc/disipador', CPU_COOLER],
            ['componentes-de-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-de-pc/gabinetes', COMPUTER_CASE],
            ['componentes-de-pc/memorias-ram-notebook', RAM],
            ['componentes-de-pc/memorias-ram-pc', RAM],
            ['componentes-de-pc/placas-madre', MOTHERBOARD],
            ['componentes-de-pc/tarjetas-de-video', VIDEO_CARD],
            ['componentes-de-pc/ventilador-pc', CASE_FAN],
            ['articulos-de-oficina/sillas-gamer', GAMING_CHAIR],
            ['accesorios-de-pc/kit-teclado-mouse', KEYBOARD_MOUSE_COMBO],
            ['accesorios-de-pc/mouse', MOUSE],
            ['accesorios-de-pc/teclado', KEYBOARD],
            ['audiovisual/audifonos', HEADPHONES],
            ['audiovisual/microfono', MICROPHONE],
            ['audiovisual/monitores', MONITOR],
            ['audiovisual/parlante', STEREO_SYSTEM],
            ['audiovisual/smart-tv', TELEVISION],
            ['celulares', CELL],
            ['celulares/celulares-y-tablets', TABLET],
            ['computadores/all-in-one', ALL_IN_ONE],
            ['computadores/consolas-de-videojuegos', VIDEO_GAME_CONSOLE],
            ['computadores/notebook', NOTEBOOK],
            ['impresoras-y-escaner/impresoras', PRINTER],
        ]
        session = session_with_proxy(extra_args)
        products_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://tecnocam.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('section', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    products_url = container.find('a')['href']
                    products_urls.append(products_url)
                page += 1
        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        add_button = soup.find('button', {'name': 'add-to-cart'})
        product_div = soup.find('div', 'type-product')
        if add_button:
            key = add_button['value']
        elif product_div:
            key = product_div['id'].split('-')[-1]
        else:
            return []

        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)

        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        sku = product_data['sku']
        description = product_data['description']
        stock_input = soup.find('input', 'qty')
        if stock_input:
            if 'max' in stock_input.attrs and stock_input['max'] != '':
                stock = int(stock_input['max'])
            else:
                stock = -1
        else:
            stock = 0
        price = Decimal(product_data['offers'][0]['price'])

        picture_urls = [tag['href'] for tag in soup.find(
            'figure', 'woocommerce-product-gallery__wrapper').findAll('a')]

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
            picture_urls=picture_urls,
            description=description
        )
        return [p]
