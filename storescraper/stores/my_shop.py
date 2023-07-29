from decimal import Decimal
import json
import logging
import validators
from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, RAM, CELL, TABLET, WEARABLE, \
    ALL_IN_ONE, USB_FLASH_DRIVE, MEMORY_CARD, PROCESSOR, MOTHERBOARD, \
    SOLID_STATE_DRIVE, STORAGE_DRIVE, VIDEO_CARD, COMPUTER_CASE, CPU_COOLER, \
    POWER_SUPPLY, KEYBOARD, MOUSE, KEYBOARD_MOUSE_COMBO, HEADPHONES, \
    STEREO_SYSTEM, MONITOR, TELEVISION, PRINTER, VIDEO_GAME_CONSOLE, \
    GAMING_CHAIR, MICROPHONE, UPS
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class MyShop(StoreWithUrlExtensions):
    url_extensions = [
        ['notebooks-de-14', NOTEBOOK],
        ['notebooks-de-156', NOTEBOOK],
        ['notebooks-de-16', NOTEBOOK],
        ['memorias-notebook', RAM],
        ['celulares', CELL],
        ['tablet', TABLET],
        ['relojes', WEARABLE],
        ['all-in-one', ALL_IN_ONE],
        ['almacenamiento-externo', USB_FLASH_DRIVE],
        ['memorias-flash', MEMORY_CARD],
        ['procesadores', PROCESSOR],
        ['placas-madres', MOTHERBOARD],
        ['memorias-ram', RAM],
        ['discos-ssd-internos', SOLID_STATE_DRIVE],
        ['discos-hdd-internos', STORAGE_DRIVE],
        ['tarjetas-de-video', VIDEO_CARD],
        ['gabinetes', COMPUTER_CASE],
        ['refrigeracion', CPU_COOLER],
        ['fuentes-de-poder', POWER_SUPPLY],
        ['teclados', KEYBOARD],
        ['mouse', MOUSE],
        ['combo-teclado-mouse', KEYBOARD_MOUSE_COMBO],
        ['audifonos-in-ear', HEADPHONES],
        ['audifonos-on-ear', HEADPHONES],
        ['parlantes', STEREO_SYSTEM],
        ['monitores', MONITOR],
        ['televisores', TELEVISION],
        ['impresion-laser', PRINTER],
        ['impresion-tinta', PRINTER],
        ['otras-impresoras', PRINTER],
        ['consolas', VIDEO_GAME_CONSOLE],
        ['audifonos-gamer', HEADPHONES],
        ['teclados-gamer', KEYBOARD],
        ['mouse-gamer', MOUSE],
        ['sillas-y-mesas', GAMING_CHAIR],
        ['microfonos', MICROPHONE],
        ['ups', UPS],
        ['servidores-nas', STORAGE_DRIVE],
        ['macbook', NOTEBOOK],
        ['imac', ALL_IN_ONE],
        ['ipad', TABLET],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 20:
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
