import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.banner_sections import TELEVISIONS
from storescraper.categories import VIDEO_GAME_CONSOLE, NOTEBOOK, \
    VIDEO_CARD, PROCESSOR, RAM, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    USB_FLASH_DRIVE, MEMORY_CARD, EXTERNAL_STORAGE_DRIVE, COMPUTER_CASE, \
    MONITOR, MOTHERBOARD, POWER_SUPPLY, KEYBOARD, MOUSE, CPU_COOLER, \
    GAMING_CHAIR, HEADPHONES, CELL, ALL_IN_ONE, TABLET, WEARABLE, PRINTER, \
    CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class TecnoPro(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_GAME_CONSOLE,
            NOTEBOOK,
            VIDEO_CARD,
            PROCESSOR,
            RAM,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            EXTERNAL_STORAGE_DRIVE,
            COMPUTER_CASE,
            MONITOR,
            MOTHERBOARD,
            POWER_SUPPLY,
            KEYBOARD,
            MOUSE,
            CPU_COOLER,
            GAMING_CHAIR,
            TELEVISIONS,
            HEADPHONES,
            CELL,
            ALL_IN_ONE,
            TABLET,
            WEARABLE,
            PRINTER,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['consolas', VIDEO_GAME_CONSOLE],
            ['notebook-y-computadores', NOTEBOOK],
            ['tarjetas-de-video', VIDEO_CARD],
            ['procesadores', PROCESSOR],
            ['memoria-ram', RAM],
            ['disco-duro', STORAGE_DRIVE],
            ['disco-ssd', SOLID_STATE_DRIVE],
            ['pendrives', USB_FLASH_DRIVE],
            ['memorias-y-pendrive', MEMORY_CARD],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['gabinetes', COMPUTER_CASE],
            ['monitores', MONITOR],
            ['placas-madres', MOTHERBOARD],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['teclados', KEYBOARD],
            ['mouses-y-teclados', MOUSE],
            ['impresora-laser', PRINTER],
            ['impresora-tinta', PRINTER],
            ['refrigeracion-cpu', CPU_COOLER],
            ['ventilador-pc', CASE_FAN],
            ['perifericos-pc', HEADPHONES],
            ['sillas-y-mesas-gamers', GAMING_CHAIR],
            ['televisores', TELEVISIONS],
            ['audifonos', HEADPHONES],
            ['iphone-1', CELL],
            ['imac', ALL_IN_ONE],
            ['macbook', NOTEBOOK],
            ['ipad', TABLET],
            ['apple-watch', WEARABLE],
            ['audifonos-apple', HEADPHONES],
            ['celulares-y-telefonia', CELL],
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
                url_webpage = 'https://tecnopro.cl/collections/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-card-grid')

                if not product_containers:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href'].split('?')[0]
                    product_urls.append('https://tecnopro.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        description = html_to_markdown(
            soup.find('div', 'product-detail-infomation').text)
        json_products = json.loads(soup.find('script', {
            'id': "ProductJson-gp-product-template-2-columns-right"}).text)
        products = []
        for variant in json_products['variants']:
            name = variant['name']
            sku = variant['sku']
            key = str(variant['id'])
            stock = -1 if variant['available'] else 0
            price = Decimal(variant['price'] / 100)
            variant_url = '{}?variant={}'.format(url, key)

            if variant['featured_image']:
                picture_urls = [variant['featured_image']['src']]
            else:
                picture_urls = None

            p = Product(
                name,
                cls.__name__,
                category,
                variant_url,
                url,
                key,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                picture_urls=picture_urls,
                description=description,
            )
            products.append(p)

        return products
