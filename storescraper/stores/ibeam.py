from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import COMPUTER_CASE, CPU_COOLER, \
    EXTERNAL_STORAGE_DRIVE, GAMING_CHAIR, HEADPHONES, KEYBOARD, \
    KEYBOARD_MOUSE_COMBO, MICROPHONE, MONITOR, MOUSE, POWER_SUPPLY, PRINTER, \
    RAM, SOLID_STATE_DRIVE, STEREO_SYSTEM, STORAGE_DRIVE, TABLET, \
    USB_FLASH_DRIVE, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Ibeam(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR,
            VIDEO_CARD,
            CPU_COOLER,
            RAM,
            COMPUTER_CASE,
            POWER_SUPPLY,
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            TABLET,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            PRINTER,
            GAMING_CHAIR,
            MICROPHONE,
            STEREO_SYSTEM
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['monitores', MONITOR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['refrigeracion', CPU_COOLER],
            ['ram', RAM],
            ['gabinetes', COMPUTER_CASE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['disco-duros-internos', STORAGE_DRIVE],
            ['disco-ssd', SOLID_STATE_DRIVE],
            ['pendrives', USB_FLASH_DRIVE],
            ['tabletas-digitales', TABLET],
            ['audifonos', HEADPHONES],
            ['mouses', MOUSE],
            ['teclados', KEYBOARD],
            ['mouse-teclados', KEYBOARD_MOUSE_COMBO],
            ['impresoras', PRINTER],
            ['sillas', GAMING_CHAIR],
            ['microfonos', MICROPHONE],
            ['audifonos-earphones', HEADPHONES],
            ['parlantes-bluetooth', STEREO_SYSTEM]
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
                url_webpage = 'https://ibeam.cl/collections/{}/' \
                              '?page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_container = soup.find('ul', 'productgrid--items')
                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_container.findAll('li'):
                    product_url = container.find(
                        'a', 'productitem--image-link')['href']
                    product_urls.append('https://ibeam.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(soup.find(
            'script', {'data-section-type': 'static-product'}).text)
        product_data = json_data['product']

        description = html_to_markdown(product_data['description'])
        picture_urls = []
        for image in product_data['media']:
            picture_urls.append(image['src'])

        products = []
        for variant in product_data['variants']:
            key = str(variant['id'])
            name = variant['name']
            sku = variant['sku']
            if variant['available']:
                stock = -1
            else:
                stock = 0

            price = (Decimal(variant['price']) / Decimal(100)).quantize(0)

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
                description=description
            )
            products.append(p)
        return products
