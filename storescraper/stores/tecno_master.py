import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, PROCESSOR, VIDEO_CARD, \
    SOLID_STATE_DRIVE, STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, RAM, \
    POWER_SUPPLY, COMPUTER_CASE, CPU_COOLER, HEADPHONES, MONITOR, MOUSE, \
    STEREO_SYSTEM, KEYBOARD, PRINTER, KEYBOARD_MOUSE_COMBO, MEMORY_CARD, \
    USB_FLASH_DRIVE, GAMING_CHAIR, GAMING_DESK, ALL_IN_ONE, NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class TecnoMaster(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            RAM,
            POWER_SUPPLY,
            COMPUTER_CASE,
            CPU_COOLER,
            HEADPHONES,
            MONITOR,
            MOUSE,
            STEREO_SYSTEM,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            PRINTER,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            GAMING_CHAIR,
            GAMING_DESK,
            ALL_IN_ONE,
            NOTEBOOK,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['sin-categorizar', MOTHERBOARD],
            ['productos/hardware/placasmadres', MOTHERBOARD],
            ['productos/hardware/procesadores', PROCESSOR],
            ['productos/almacenamiento/discosestadosolidosdd',
             SOLID_STATE_DRIVE],
            ['productos/almacenamiento/discosduroshdd', STORAGE_DRIVE],
            ['productos/almacenamiento/discosdurosecternos',
             EXTERNAL_STORAGE_DRIVE],
            ['productos/hardware/memorias-ram', RAM],
            ['productos/hardware/fuentesdepoder', POWER_SUPPLY],
            ['productos/hardware/gabinetes', COMPUTER_CASE],
            ['productos/hardware/refrigeracion-ventiladores', CPU_COOLER],
            ['productos/perifericos/audifonos', HEADPHONES],
            ['productos/perifericos/monitores', MONITOR],
            ['productos/perifericos/mouse', MOUSE],
            ['productos/perifericos/parlantes', STEREO_SYSTEM],
            ['productos/perifericos/teclados', KEYBOARD],
            ['productos/perifericos/kit_tecladosymouse',
             KEYBOARD_MOUSE_COMBO],
            ['productos/perifericos/impresoras', PRINTER],
            ['productos/almacenamiento/tarjetasdememoriasdd', MEMORY_CARD],
            ['productos/almacenamiento/flash-drivers-usb', USB_FLASH_DRIVE],
            ['productos/hardware/tarjetasdevideo', VIDEO_CARD],
            ['sillasgamer', GAMING_CHAIR],
            ['productos/perifericos/microfonosystreaming', GAMING_DESK],
            ['pc_armados/pc-escritorio', ALL_IN_ONE],
            ['pc_armados/notebook-laptop', NOTEBOOK],
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

                url_webpage = 'https://tecno-master.cl/categoria-producto/' + \
                              url_extension

                if page > 1:
                    url_webpage += '/page/{}'.format(page)
                print(url_webpage)
                response = session.get(url_webpage)

                if response.status_code == 404:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                product_containers = soup.find('ul', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for container in product_containers.findAll(
                        'li', 'type-product'):
                    product_url = container.find(
                        'a', 'woocommerce-LoopProduct-link woocommerce-'
                             'loop-product__link')['href']
                    product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name_tag = soup.find('h1')

        if not name_tag:
            return []

        name = name_tag.text
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        sku_tag = soup.find('span', 'sku')

        if sku_tag:
            sku = soup.find('span', 'sku').text.strip()
        else:
            sku = None

        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        elif soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = -1
        price_container = soup.find('p', 'price')

        if not price_container.text:
            return []

        elif price_container.find('ins'):
            price = Decimal(remove_words(price_container.find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))
        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'elementor-widget-image').findAll('img')]
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
            picture_urls=picture_urls
        )
        return [p]
