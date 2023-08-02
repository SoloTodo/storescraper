from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import COMPUTER_CASE, EXTERNAL_STORAGE_DRIVE, \
    GAMING_CHAIR, HEADPHONES, KEYBOARD, KEYBOARD_MOUSE_COMBO, MEMORY_CARD, \
    MONITOR, MOTHERBOARD, MOUSE, NOTEBOOK, POWER_SUPPLY, PRINTER, PROCESSOR, \
    RAM, SOLID_STATE_DRIVE, STEREO_SYSTEM, STORAGE_DRIVE, USB_FLASH_DRIVE, \
    VIDEO_CARD, TABLET, ALL_IN_ONE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class Lifemax(StoreWithUrlExtensions):
    url_extensions = [
        ['audifonos-bluetooth', HEADPHONES],
        ['audifonos-con-cable', HEADPHONES],
        ['tarjeta-de-memoria-microsdxc', MEMORY_CARD],
        ['tarjeta-de-memoria-microsd', MEMORY_CARD],
        ['tarjeta-de-memoria-microsdhc', MEMORY_CARD],
        ['discos-ssd', SOLID_STATE_DRIVE],
        ['discos-ssd-m-2', SOLID_STATE_DRIVE],
        ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
        ['memoria-ram-notebook', RAM],
        ['memoria-ram-pc', RAM],
        ['disco-duro-interno', STORAGE_DRIVE],
        ['disco-ssd-externo', EXTERNAL_STORAGE_DRIVE],
        ['monitores', MONITOR],
        ['notebook-corporativos', NOTEBOOK],
        ['impresoras-multifuncionales-tinta', PRINTER],
        ['impresoras-laser', PRINTER],
        ['pendrives', USB_FLASH_DRIVE],
        ['tablets', TABLET],
        ['all-in-one', ALL_IN_ONE],
        ['mouse', MOUSE],
        ['kits-de-mouse-y-teclado', KEYBOARD_MOUSE_COMBO],
        ['teclados', KEYBOARD],
        ['memorias-ram-pc-gaming', RAM],
        ['memoria-ram-notebook-gamers', RAM],
        ['ssd-m-2-especial-gamers', SOLID_STATE_DRIVE],
        ['monitores-gamer', MONITOR],
        ['procesadores', PROCESSOR],
        ['gabinetes-gamer', COMPUTER_CASE],
        ['placas-madre', MOTHERBOARD],
        ['mouse-gamers', MOUSE],
        ['fuentes-de-poder', POWER_SUPPLY],
        ['sillas-gamer', GAMING_CHAIR],
        ['tarjeta-de-video', VIDEO_CARD],
        ['audifonos-gamers', HEADPHONES],
        ['disco-duro-externo-especial-gamer', EXTERNAL_STORAGE_DRIVE],
        ['parlantes-y-subwoofers', STEREO_SYSTEM],
        ['audifonos-c-microfono', HEADPHONES],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            if page > 10:
                raise Exception('Page overflow: ' + url_extension)

            page_url = 'https://www.lifemaxstore.cl/collection/{}/' \
                       '?page={}'.format(url_extension, page)
            print(page_url)
            response = session.get(page_url)
            data = response.text
            soup = BeautifulSoup(data, 'html5lib')
            product_container = soup.find('div', 'bs-collection')

            if not product_container:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break

            product_containers = product_container.findAll(
                'div', 'bs-collection__product')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(
                    'https://www.lifemaxstore.cl' + product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.text == "":
            return []

        soup = BeautifulSoup(response.text, 'html5lib')

        json_container = soup.find('main', 'bs-main').find(
            'script').string.strip()
        json_container = json.loads(
            re.search(r"window.INIT.products.push\(([\s\S]+)\);",
                      json_container).groups()[0])

        product_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json',
                       'data-schema': 'Product'}).string)

        picture_urls = product_data['image']

        base_name = json_container['product']['title']
        description = html_to_markdown(
            json_container['product']['description'])

        products = []
        for variant in json_container['variants']:
            name = base_name + ' ' + variant['title']
            key = str(variant['id'])
            sku = variant['sku']
            stock = int(variant['stock'][0]['quantityAvailable'])
            normal_price = Decimal(variant['finalPrice'])
            offer_price = (normal_price * Decimal('0.97')).quantize(0)

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
            products.append(p)

        return products
