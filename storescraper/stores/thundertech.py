from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup

from storescraper.categories import PROCESSOR, MOTHERBOARD, RAM, \
    SOLID_STATE_DRIVE, STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, MEMORY_CARD, \
    USB_FLASH_DRIVE, VIDEO_CARD, POWER_SUPPLY, CPU_COOLER, MONITOR, KEYBOARD, \
    MOUSE, HEADPHONES, STEREO_SYSTEM, KEYBOARD_MOUSE_COMBO, PRINTER, NOTEBOOK, \
    TABLET, WEARABLE, ALL_IN_ONE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class Thundertech(StoreWithUrlExtensions):
    url_extensions = [
        ['procesador', PROCESSOR],
        ['placa-madre', MOTHERBOARD],
        ['memorias-ram', RAM],
        ['disco-estado-solido', SOLID_STATE_DRIVE],
        ['disco-duro-notebook', STORAGE_DRIVE],
        ['disco-duro-pcs', STORAGE_DRIVE],
        ['nas', SOLID_STATE_DRIVE],
        ['discos-portatiles', EXTERNAL_STORAGE_DRIVE],
        ['discos-sobremesa', EXTERNAL_STORAGE_DRIVE],
        ['memorias-flash', MEMORY_CARD],
        ['pendrive', USB_FLASH_DRIVE],
        ['tarjeta-de-video', VIDEO_CARD],
        ['componentes/fuentes-de-poder', POWER_SUPPLY],
        ['componentes/disipadores', CPU_COOLER],
        ['monitores', MONITOR],
        ['teclados', KEYBOARD],
        ['mouse', MOUSE],
        ['audifonos', HEADPHONES],
        ['parlantes', STEREO_SYSTEM],
        ['kit-perifericos', KEYBOARD_MOUSE_COMBO],
        ['impresoras', PRINTER],
        ['mac', NOTEBOOK],
        ['macbook', NOTEBOOK],
        ['ipad', TABLET],
        ['watch', WEARABLE],
        ['accesorios-1', KEYBOARD],
        ['todo-en-uno', ALL_IN_ONE],
        ['portatiles', NOTEBOOK],
        ['tableta', TABLET],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('Page overflow: ' + url_extension)
            url_webpage = 'https://www.thundertech.cl/{}?page={}'.format(
                url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('div', 'product-block')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = 'https://www.thundertech.cl' + container.find('a')['href']
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
        for entry in json_data:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        key = soup.find('meta', {'property': 'og:id'})['content']

        stock = -1 if product_data['offers']['availability'] == 'http://schema.org/InStock' else 0
        price = Decimal(product_data['offers']['price']).quantize(0)
        sku = product_data['sku']
        picture_urls = [product_data['image']]
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
