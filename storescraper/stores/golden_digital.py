import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, COMPUTER_CASE, CPU_COOLER, \
    EXTERNAL_STORAGE_DRIVE, GAMING_DESK, HEADPHONES, KEYBOARD, \
    KEYBOARD_MOUSE_COMBO, MONITOR, MOTHERBOARD, MOUSE, NOTEBOOK, \
    POWER_SUPPLY, PRINTER, PROCESSOR, RAM, SOLID_STATE_DRIVE, STEREO_SYSTEM, \
    STORAGE_DRIVE, TELEVISION, USB_FLASH_DRIVE, UPS, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class GoldenDigital(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            HEADPHONES,
            STEREO_SYSTEM,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_CARD,
            NOTEBOOK,
            ALL_IN_ONE,
            PRINTER,
            MONITOR,
            GAMING_DESK,
            TELEVISION,
            KEYBOARD_MOUSE_COMBO,
            MOUSE,
            KEYBOARD,
            UPS
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento/disco-externo', EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento/discos-de-estado-solido', SOLID_STATE_DRIVE],
            ['almacenamiento/discos-duros-internos', STORAGE_DRIVE],
            ['almacenamiento/pendrive', USB_FLASH_DRIVE],
            ['audio/audifonos', HEADPHONES],
            ['audio/parlantes', STEREO_SYSTEM],
            ['componentes-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-pc/gabinetes', COMPUTER_CASE],
            ['memoria-ram-notebook', RAM],
            ['componentes-pc/memoria-ram-pc', RAM],
            ['componentes-pc/placa-madre', MOTHERBOARD],
            ['componentes-pc/procesadores', PROCESSOR],
            ['componentes-pc/refrigeracion', CPU_COOLER],
            ['componentes-pc/tarjeta-de-video', VIDEO_CARD],
            ['computadores/notebooks', NOTEBOOK],
            ['computadores/pc-all-in-one', ALL_IN_ONE],
            ['impresoras', PRINTER],
            ['monitores-y-proyectores', MONITOR],
            ['sillas-y-escritorios/escritorio-gamer', GAMING_DESK],
            ['smart-tv', TELEVISION],
            ['teclados-y-mouse/kit-teclado-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['teclados-y-mouse/mouse', MOUSE],
            ['teclados-y-mouse/teclados', KEYBOARD],
            ['ups-y-respaldo-energia', UPS]
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
                url_webpage = 'https://www.goldendigital.cl/categoria/{}/' \
                              '?product-page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a', 'woocommerce-Loop'
                                                      'Product-link')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[-1]

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        if '@graph' not in json_data:
            return []

        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        sku = str(product_data['sku'])
        description = product_data['description']
        offer_price = Decimal(product_data['offers'][0]['price'])
        normal_price = (offer_price * Decimal(1.05)).quantize(0)

        qty_input = soup.find('input', 'input-text qty text')
        if qty_input:
            if qty_input['max']:
                stock = int(qty_input['max'])
            else:
                stock = -1
        else:
            if soup.find('button', 'single_add_to_cart_button'):
                stock = 1
            else:
                stock = 0

        if 'image' in product_data:
            picture_urls = [product_data['image']]
        else:
            picture_urls = []

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
            part_number=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
