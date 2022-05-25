import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import NOTEBOOK, ALL_IN_ONE, TABLET, \
    STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, SOLID_STATE_DRIVE, MEMORY_CARD, \
    USB_FLASH_DRIVE, PROCESSOR, COMPUTER_CASE, POWER_SUPPLY, MOTHERBOARD, \
    RAM, VIDEO_CARD, MOUSE, PRINTER, HEADPHONES, STEREO_SYSTEM, UPS, MONITOR, \
    KEYBOARD_MOUSE_COMBO, KEYBOARD, PROJECTOR, GAMING_CHAIR


class Cintegral(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            ALL_IN_ONE,
            TABLET,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            PROCESSOR,
            COMPUTER_CASE,
            POWER_SUPPLY,
            MOTHERBOARD,
            RAM,
            VIDEO_CARD,
            MOUSE,
            PRINTER,
            HEADPHONES,
            STEREO_SYSTEM,
            UPS,
            MONITOR,
            KEYBOARD_MOUSE_COMBO,
            KEYBOARD,
            PROJECTOR,
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://cintegral.cl/{}-?page={}'

        url_extensions = [
            ['24', NOTEBOOK],  # Notebooks
            ['25', ALL_IN_ONE],  # All in One
            ['27', TABLET],  # Tablet
            ['94', GAMING_CHAIR],
            ['66', STORAGE_DRIVE],  # Discos duros PC
            ['67', EXTERNAL_STORAGE_DRIVE],  # Discos duros externos
            ['68', SOLID_STATE_DRIVE],  # Unidades de estado sólido
            ['69', MEMORY_CARD],  # Memorias Flash
            ['70', USB_FLASH_DRIVE],  # Pendrive
            ['31', PROCESSOR],  # Procesadores
            ['33', POWER_SUPPLY],  # Fuentes de poder
            ['34', MOTHERBOARD],  # Placas madre
            ['36', VIDEO_CARD],  # Tarjetas de video
            ['35', RAM],
            ['32', COMPUTER_CASE],  # Gabinetes
            ['18', MONITOR],  # Monitores
            ['56', PROJECTOR],  # Proyectores
            ['15', PRINTER],
            ['59', HEADPHONES],  # Audífonos / Micrófonos
            ['60', STEREO_SYSTEM],  # Parlantes
            ['61', UPS],  # UPS
            ['38', KEYBOARD],  # Teclados
            ['40', MOUSE],  # Mouse
            ['39', KEYBOARD_MOUSE_COMBO],  # Combos teclado mouse
            ['112', NOTEBOOK],  # Notebooks gamer
            ['124', MONITOR],  # Monitores gamer
            ['113', GAMING_CHAIR],
            ['114', MOUSE],  # Periféricos gamer
            ['115', VIDEO_CARD],  # Tarjetas de video gamer
            ['116', PROCESSOR],  # Procesadores gamer
            ['117', RAM],  # RAM gamer
            ['118', MOTHERBOARD],  # Placas madre gamer
            ['119', COMPUTER_CASE],  # Gabinetes gamer
            ['120', SOLID_STATE_DRIVE],  # Almacenamiento gamer
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + url_extension)

                url = url_base.format(url_extension, page)
                source = session.get(url, verify=False).text
                soup = BeautifulSoup(source, 'html.parser')
                product_tags = soup.findAll('article', 'item')

                if not product_tags:
                    if page == 1:
                        logging.warning('Empty category: ' + url)
                    break

                for product_tag in product_tags:
                    product_url = product_tag.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url, verify=False).text
        soup = BeautifulSoup(page_source, 'html.parser')
        product_json_tag = soup.find('div', {'id': 'product-details'})
        product_json = json.loads(product_json_tag['data-product'])
        stock = product_json['quantity']
        key = str(product_json['id'])
        description = html_to_markdown(product_json['description'])
        sku = product_json['reference']
        name = product_json['name']
        price = Decimal(product_json['price_amount'])
        picture_urls = [x['large']['url'] for x in product_json['images']]

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
