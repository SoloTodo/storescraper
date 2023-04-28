from decimal import Decimal
import json
import logging
import validators
from bs4 import BeautifulSoup
from storescraper.categories import *
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MyShop(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            STEREO_SYSTEM,
            MONITOR,
            TELEVISION,
            CELL,
            WEARABLE,
            NOTEBOOK,
            ALL_IN_ONE,
            TABLET,
            USB_FLASH_DRIVE,
            PRINTER,
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            COMPUTER_CASE,
            CPU_COOLER,
            POWER_SUPPLY,
            MOUSE,
            GAMING_CHAIR,
            MICROPHONE,
            VIDEO_GAME_CONSOLE,
            MEMORY_CARD,
            KEYBOARD,
            UPS,
            STORAGE_DRIVE,
            KEYBOARD_MOUSE_COMBO,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['portabilidad/notebooks-de-14', NOTEBOOK],
            ['portabilidad/notebooks-de-156', NOTEBOOK],
            ['portabilidad/notebooks-de-16', NOTEBOOK],
            ['portabilidad/memorias-notebook', RAM],
            ['portabilidad/celulares', CELL],
            ['portabilidad/tablet', TABLET],
            ['portabilidad/relojes', WEARABLE],
            ['computacion/all-in-one', ALL_IN_ONE],
            ['computacion/almacenamiento-externo', USB_FLASH_DRIVE],
            ['computacion/memorias-flash', MEMORY_CARD],
            ['partes-y-piezas/procesadores', PROCESSOR],
            ['partes-y-piezas/placas-madres', MOTHERBOARD],
            ['partes-y-piezas/memorias-ram', RAM],
            ['partes-y-piezas/discos-ssd-internos', SOLID_STATE_DRIVE],
            ['partes-y-piezas/discos-hdd-internos', STORAGE_DRIVE],
            ['partes-y-piezas/tarjetas-de-video', VIDEO_CARD],
            ['partes-y-piezas/gabinetes', COMPUTER_CASE],
            ['partes-y-piezas/refrigeracion', CPU_COOLER],
            ['partes-y-piezas/fuentes-de-poder', POWER_SUPPLY],
            ['partes-y-piezas/teclados', KEYBOARD],
            ['partes-y-piezas/mouse', MOUSE],
            ['partes-y-piezas/combo-teclado-mouse', KEYBOARD_MOUSE_COMBO],
            ['audio-video/audifonos-in-ear', HEADPHONES],
            ['audio-video/audifonos-on-ear', HEADPHONES],
            ['audio-video/parlantes', STEREO_SYSTEM],
            ['audio-video/monitores', MONITOR],
            ['audio-video/televisores', TELEVISION],
            ['impresion/impresion-laser', PRINTER],
            ['impresion/impresion-tinta', PRINTER],
            ['impresion/otras-impresoras', PRINTER],
            ['gamer/consolas', VIDEO_GAME_CONSOLE],
            ['gamer/audifonos-gamer', HEADPHONES],
            ['gamer/teclados-gamer', KEYBOARD],
            ['gamer/mouse-gamer', MOUSE],
            ['gamer/sillas-y-mesas', GAMING_CHAIR],
            ['gamer/microfonos', MICROPHONE],
            ['empresas/ups', UPS],
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
                url_webpage = 'https://www.myshop.cl/categorias/{}'\
                              '/page/{}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html5lib')
                collection = soup.find('div', 'products')
                if not collection:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                product_containers = collection.findAll('div', 'product')
                for container in product_containers:
                    product_url = container.find(
                        'h3', 'product-title').find('a')['href']
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

        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)
        for entry in json_data['@graph']:
            if '@type' in entry and entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        sku = product_data['sku']
        description = product_data['description']
        offer_price = Decimal(product_data['offers'][0]['price'])
        normal_price = (offer_price * Decimal('1.03')).quantize(0)

        stock_p = soup.find('p', 'stock in-stock')
        if stock_p:
            if 'más de' in stock_p.text.lower():
                stock = -1
            else:
                stock = int(stock_p.text.split(' ')[0])
        else:
            stock = 0

        part_number_tag = soup.find('span', 'custom-part_number')
        if part_number_tag:
            part_number = part_number_tag.find('span').text.strip()
        else:
            part_number = None

        picture_urls = []
        picture_container = soup.find(
            'figure', 'woocommerce-product-gallery__wrapper')
        for i in picture_container.findAll('img'):
            if validators.url(i['src']):
                picture_urls.append(i['src'])

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
            picture_urls=picture_urls,
            description=description,
            part_number=part_number
        )
        return [p]
