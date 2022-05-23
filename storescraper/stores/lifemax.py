from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import COMPUTER_CASE, EXTERNAL_STORAGE_DRIVE, \
    GAMING_CHAIR, HEADPHONES, KEYBOARD, KEYBOARD_MOUSE_COMBO, MEMORY_CARD, \
    MONITOR, MOTHERBOARD, MOUSE, NOTEBOOK, POWER_SUPPLY, PRINTER, PROCESSOR, \
    RAM, SOLID_STATE_DRIVE, STEREO_SYSTEM, STORAGE_DRIVE, USB_FLASH_DRIVE, \
    VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Lifemax(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            EXTERNAL_STORAGE_DRIVE,
            GAMING_CHAIR, HEADPHONES,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            MEMORY_CARD,
            MONITOR,
            MOTHERBOARD,
            MOUSE,
            NOTEBOOK,
            POWER_SUPPLY,
            PRINTER,
            PROCESSOR,
            RAM,
            SOLID_STATE_DRIVE,
            STEREO_SYSTEM,
            STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            VIDEO_CARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['audifonos-bluetooth', HEADPHONES],
            ['audifonos-con-cable', HEADPHONES],
            ['tarjeta-de-memoria-microsdxc', MEMORY_CARD],
            ['tarjeta-de-memoria-microsd', MEMORY_CARD],
            ['discos-ssd', SOLID_STATE_DRIVE],
            ['discos-ssd-m-2', SOLID_STATE_DRIVE],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['disco-duro-interno', STORAGE_DRIVE],
            ['memoria-ram-notebook', RAM],
            ['memoria-ram-pc', RAM],
            ['impresoras-multifuncionales-tinta', PRINTER],
            ['notebook-corporativos', NOTEBOOK],
            ['mouse', MOUSE],
            ['kits-de-mouse-y-teclado', KEYBOARD_MOUSE_COMBO],
            ['teclados', KEYBOARD],
            ['pendrives', USB_FLASH_DRIVE],
            ['monitores', MONITOR],
            ['memorias-ram-pc-gaming', RAM],
            ['memoria-ram-notebook-gamers', RAM],
            ['audifonos-gamers', HEADPHONES],
            ['sillas-gamer', GAMING_CHAIR],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['procesadores', PROCESSOR],
            ['ssd-m-2-especial-gamers', SOLID_STATE_DRIVE],
            ['tarjeta-de-video', VIDEO_CARD],
            ['placas-madre', MOTHERBOARD],
            ['monitores-gamer', MONITOR],
            ['mouse-gamers', MOUSE],
            ['gabinetes-gamer', COMPUTER_CASE],
            ['audifonos-c-microfono', HEADPHONES],
            ['parlantes-y-subwoofers', STEREO_SYSTEM],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if category != local_category:
                continue

            page = 1

            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + category_path)

                page_url = 'https://www.lifemaxstore.cl/collection/{}/' \
                           '?page={}'.format(category_path, page)
                print(page_url)
                response = session.get(page_url)
                data = response.text
                soup = BeautifulSoup(data, 'html.parser')
                product_container = soup.find('article')

                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + category_path)
                    break

                product_containers = product_container.findAll('a', 'col-sm-6')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + category_path)
                    break

                for container in product_containers:
                    product_url = container['href']
                    product_urls.append(
                        'https://www.lifemaxstore.cl' + product_url)

                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')

        json_container = soup.find('main', 'bs-main').find(
            'script').text.strip()
        json_container = json.loads(
            re.search(r"window.INIT.products.push\(([\s\S]+)\);",
                      json_container).groups()[0])

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

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
            price = Decimal(variant['finalPrice'])

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
            products.append(p)

        return products
