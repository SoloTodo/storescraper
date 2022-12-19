import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import EXTERNAL_STORAGE_DRIVE, TABLET, \
    SOLID_STATE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, RAM, MOTHERBOARD, \
    PROCESSOR, VIDEO_CARD, CPU_COOLER, NOTEBOOK, MONITOR, HEADPHONES, MOUSE, \
    STEREO_SYSTEM, KEYBOARD, UPS, VIDEO_GAME_CONSOLE, GAMING_CHAIR, \
    GAMING_DESK, MICROPHONE, USB_FLASH_DRIVE, ALL_IN_ONE, STORAGE_DRIVE, \
    MEMORY_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Jasaltec(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            CPU_COOLER,
            NOTEBOOK,
            MONITOR,
            HEADPHONES,
            MOUSE,
            STEREO_SYSTEM,
            KEYBOARD,
            UPS,
            VIDEO_GAME_CONSOLE,
            GAMING_CHAIR,
            GAMING_DESK,
            MICROPHONE,
            TABLET,
            ALL_IN_ONE,
            STORAGE_DRIVE,
            MEMORY_CARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento-de-datos/disco-estado-solido-externo',
             EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento-de-datos/disco-estado-solido-interno',
             SOLID_STATE_DRIVE],
            ['almacenamiento-de-datos/disco-mecanico-interno',
             STORAGE_DRIVE],
            ['componentes-informaticos/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-informaticos/gabinetes', COMPUTER_CASE],
            ['componentes-informaticos/procesadores', PROCESSOR],
            ['componentes-informaticos/tarjeta-madre', MOTHERBOARD],
            ['componentes-informaticos/tarjetas-graficas', VIDEO_CARD],
            ['componentes-informaticos/ventiladores-y-enfriadores',
             CPU_COOLER],
            ['memoria-ram/modulos-ram-notebook', RAM],
            ['memoria-ram/modulos-ram-pc-escritorio', RAM],
            ['memoria-ram/pendrive', USB_FLASH_DRIVE],
            ['memoria-ram/tarjetas-de-memoria-flash', MEMORY_CARD],
            ['almacenamiento-de-datos/memoria-ram/pendrive', USB_FLASH_DRIVE],
            ['computadores/all-in-one', ALL_IN_ONE],
            ['computadores/notebook', NOTEBOOK],
            ['computadores/notebook-gamer', NOTEBOOK],
            ['computadores/tabletas', TABLET],
            ['perifericos/audifonos', HEADPHONES],
            ['perifericos/microfonos', MICROPHONE],
            ['perifericos/mouses', MOUSE],
            ['perifericos/parlantes', STEREO_SYSTEM],
            ['perifericos/teclados', KEYBOARD],
            ['monitores', MONITOR],
            ['respaldo-energia/ups', UPS],
            ['sillas', GAMING_CHAIR],
            ['videojuegos/consola', VIDEO_GAME_CONSOLE],
            ['escritorios', GAMING_DESK],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 15:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://jasaltec.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)

                if response.status_code == 404 and page == 1:
                    raise Exception(url_webpage)

                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-grid-item')

                if not product_containers:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        if "PAGE NOT FOUND" in soup.text:
            return []

        name = soup.find('h1', 'product_title').text
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        sku_tag = soup.find('span', 'sku')

        if sku_tag:
            sku = soup.find('span', 'sku').text.strip()
        else:
            sku = None

        if soup.find('p', 'out-of-stock') or \
                soup.find('p', 'available-on-backorder'):
            stock = 0
        else:
            stock = -1

        if soup.find('p', 'price').text == "":
            return []

        if soup.find('p', 'price').find('ins'):
            offer_price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            offer_price = Decimal(remove_words(
                soup.find('p', 'price').find('bdi').text))

        normal_price = (offer_price / Decimal('0.943')).quantize(0)
        picture_urls = [tag['src'] for tag in soup.find('div',
                                                        'woocommerce-product'
                                                        '-gallery').findAll(
            'img')]
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
        )
        return [p]
