import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, KEYBOARD, MONITOR, HEADPHONES, \
    MEMORY_CARD, CELL, SOLID_STATE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, \
    VIDEO_CARD, MOTHERBOARD, RAM, PROCESSOR, USB_FLASH_DRIVE, STEREO_SYSTEM, \
    TELEVISION, PRINTER, GAMING_CHAIR, STORAGE_DRIVE, TABLET, NOTEBOOK, \
    MICROPHONE, GAMING_DESK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class ElectroVentas(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            KEYBOARD,
            MONITOR,
            HEADPHONES,
            MEMORY_CARD,
            CELL,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            VIDEO_CARD,
            MOTHERBOARD,
            RAM,
            PROCESSOR,
            USB_FLASH_DRIVE,
            STEREO_SYSTEM,
            TELEVISION,
            PRINTER,
            GAMING_CHAIR,
            STORAGE_DRIVE,
            TABLET,
            NOTEBOOK,
            MICROPHONE,
            GAMING_DESK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['televisores', TELEVISION],
            ['parlantes', STEREO_SYSTEM],
            ['audifonos', HEADPHONES],
            ['monitores', MONITOR],
            ['mouses-y-accesorios-gaming', MOUSE],
            ['teclados-y-accesorios', KEYBOARD],
            ['sillas-gaming', GAMING_CHAIR],
            ['placas-madre', MOTHERBOARD],
            ['unidades-de-almacenamiento', SOLID_STATE_DRIVE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes-gaming', COMPUTER_CASE],
            ['tarjetas-de-video', VIDEO_CARD],
            ['tarjetas-de-memoria', MEMORY_CARD],
            ['discos-duros', STORAGE_DRIVE],
            ['pendrives', USB_FLASH_DRIVE],
            ['tablets', TABLET],
            ['impresoras', PRINTER],
            ['celulares', CELL],
            ['teclados-gaming', KEYBOARD],
            ['notebooks', NOTEBOOK],
            ['microfonos', MICROPHONE],
            ['escritorios-gamer', GAMING_DESK]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 20:
                    raise Exception('Page overflow')

                url_webpage = 'https://electroventas.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find(
                    'div', {'id': 'js-product-list'})

                if not product_containers or not product_containers.findAll(
                        'article', 'product-miniature'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for container in product_containers.findAll(
                        'article', 'product-miniature'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.url != url:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        product_data_tag = soup.findAll(
            'script', {'type': 'application/ld+json'})[2]
        product_data = json.loads(product_data_tag.text
                                  .replace('\u000a', ''))
        name = product_data['name']
        sku = product_data['mpn']
        price = Decimal(product_data['offers']['price'])
        picture_urls = product_data['offers'].get('image', None)
        stock_container = soup.find('div', 'product-quantities')

        if stock_container:
            stock = int(stock_container.find('span')['data-stock'])
        else:
            stock = 0

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
