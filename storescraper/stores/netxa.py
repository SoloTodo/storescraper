from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    CELL, COMPUTER_CASE, CPU_COOLER, GAMING_CHAIR, HEADPHONES, KEYBOARD, MONITOR, MOTHERBOARD, MOUSE, NOTEBOOK,
    POWER_SUPPLY, PROCESSOR, RAM, SOLID_STATE_DRIVE, STORAGE_DRIVE, TABLET, VIDEO_CARD, EXTERNAL_STORAGE_DRIVE,
    USB_FLASH_DRIVE, WEARABLE, ALL_IN_ONE, KEYBOARD_MOUSE_COMBO, STEREO_SYSTEM, TELEVISION, PRINTER,
    VIDEO_GAME_CONSOLE, MEMORY_CARD)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class Netxa(StoreWithUrlExtensions):
    url_extensions = [
        ['discos-de-estado-solido-externos', EXTERNAL_STORAGE_DRIVE],
        ['discos-de-estado-solido-internos', SOLID_STATE_DRIVE],
        ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
        ['discos-duros-internos', STORAGE_DRIVE],
        ['celulares-desbloqueados', CELL],
        ['cajas-gabinetes', COMPUTER_CASE],
        ['fuentes-de-poder', POWER_SUPPLY],
        ['procesadores', PROCESSOR],
        ['tarjetas-de-video', VIDEO_CARD],
        ['tarjetas-madre-placas-madre', MOTHERBOARD],
        ['ventiladores-y-sistemas-de-enfriamiento', CPU_COOLER],
        ['2-en-1', NOTEBOOK],
        ['portatiles', NOTEBOOK],
        ['tableta', TABLET],
        ['todo-en-uno', ALL_IN_ONE],
        ['impresoras-ink-jet', PRINTER],
        ['impresoras-laser', PRINTER],
        ['impresoras-multifuncionales', PRINTER],
        ['modulos-ram-genericos', RAM],
        ['modulos-ram-propietarios', RAM],
        ['tarjetas-de-memoria-flash', MEMORY_CARD],
        ['unidades-flash-usb', USB_FLASH_DRIVE],
        ['sillas', GAMING_CHAIR],
        ['monitores', MONITOR],
        ['televisores', TELEVISION],
        ['auriculares-y-manos-libres', HEADPHONES],
        ['combos-de-teclado-y-raton', KEYBOARD_MOUSE_COMBO],
        ['parlantes-bocinas-cornetas', STEREO_SYSTEM],
        ['ratones', MOUSE],
        ['teclados-y-teclados-de-numeros', KEYBOARD],
        ['audio-gamer', HEADPHONES],
        ['monitor-gamer', MONITOR],
        ['mouse-teclado-gamer', MOUSE],
        ['notebook-gamer', NOTEBOOK],
        ['tarjeta-video-gamer', VIDEO_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://netxa.cl/categoria-producto/{}/page/{}/'.format(
                              url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)

            if response.status_code == 404:
                if page == 1:
                    logging.warning('empty category: ' + url_extension)
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.find('ul', 'products').findAll('li', 'product')
            for container in product_containers:
                product_url = container.find('a', 'woocommerce-LoopProduct-link')['href']
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)
        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[-1]
        price = Decimal(product_data['offers'][0]['price'])
        if product_data['offers'][0]['availability'] == 'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0
        sku = product_data['sku']
        if 'image' in product_data:
            picture_urls = [product_data['image']]
        else:
            picture_urls = None
        description = product_data['description']

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
            part_number=sku
        )
        return [p]
