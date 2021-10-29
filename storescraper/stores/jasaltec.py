import logging

from bs4 import BeautifulSoup

from storescraper.categories import EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, \
    SOLID_STATE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, RAM, MOTHERBOARD, \
    PROCESSOR, VIDEO_CARD, CPU_COOLER, NOTEBOOK, MONITOR, HEADPHONES, MOUSE, \
    STEREO_SYSTEM, KEYBOARD, UPS, VIDEO_GAME_CONSOLE, VIDEO_GAME, GAMING_CHAIR
from storescraper.store import Store
from storescraper.utils import session_with_proxy


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
            VIDEO_GAME,
            GAMING_CHAIR,

        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento-de-datos/hdd-externo', EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento-de-datos/pendrive', USB_FLASH_DRIVE],
            ['almacenamiento-de-datos/ssd', SOLID_STATE_DRIVE],
            ['almacenamiento-de-datos/ssd-externo', SOLID_STATE_DRIVE],
            ['componentes-informaticos/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-informaticos/gabinetes', COMPUTER_CASE],
            ['componentes-informaticos/memoria-ram', RAM],
            ['componentes-informaticos/placas-madres', MOTHERBOARD],
            ['componentes-informaticos/procesadores', PROCESSOR],
            ['componentes-informaticos/tarjetas-de-videos', VIDEO_CARD],
            ['componentes-informaticos/ventiladores-y-enfriadores',
             CPU_COOLER],
            ['computadores/notebook', NOTEBOOK],
            ['monitores', MONITOR],
            ['perifericos/audifonos', HEADPHONES],
            ['perifericos/mouses', MOUSE],
            ['perifericos/parlantes', STEREO_SYSTEM],
            ['perifericos/teclados', KEYBOARD],
            ['respaldo-energia/ups', UPS],
            ['videojuegos/consola', VIDEO_GAME_CONSOLE],
            ['videojuegos/juegos', VIDEO_GAME],
            ['sillas', GAMING_CHAIR],
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
                url_webpage = 'https://jasaltec.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
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
