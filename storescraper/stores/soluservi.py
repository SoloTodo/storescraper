import logging

from bs4 import BeautifulSoup

from storescraper.categories import EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, \
    SOLID_STATE_DRIVE, KEYBOARD_MOUSE_COMBO, TABLET, MOUSE, NOTEBOOK, \
    WEARABLE, HEADPHONES, STEREO_SYSTEM, ALL_IN_ONE, RAM, VIDEO_GAME_CONSOLE, \
    PRINTER, MEMORY_CARD, USB_FLASH_DRIVE, MONITOR, TELEVISION
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Soluservi(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            KEYBOARD_MOUSE_COMBO,
            TABLET,
            MOUSE,
            NOTEBOOK,
            WEARABLE,
            HEADPHONES,
            STEREO_SYSTEM,
            ALL_IN_ONE,
            RAM,
            VIDEO_GAME_CONSOLE,
            PRINTER,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            MONITOR,
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento-componentes-para-pc/disco-duro-externo',
             EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento-componentes-para-pc/disco-duro-interno',
             STORAGE_DRIVE],
            ['almacenamiento-componentes-para-pc/unidad-estado-solido-ssd',
             SOLID_STATE_DRIVE],
            ['accesorios-2/kit-teclados-mouse', KEYBOARD_MOUSE_COMBO],
            ['mouse', MOUSE],
            ['apple/ipad', TABLET],
            ['apple/mac', NOTEBOOK],
            ['apple/watch', WEARABLE],
            ['audio-y-video/audifonos', HEADPHONES],
            ['audio-y-video/parlantes-audio-y-video', STEREO_SYSTEM],
            ['escritorio/all-in-one', ALL_IN_ONE],
            ['memorias/memoria-ram-notebok', RAM],
            ['consolas', VIDEO_GAME_CONSOLE],
            ['impresoras-y-escaneres/impresora-laser', PRINTER],
            ['impresoras-y-escaneres/multifuncional', PRINTER],
            ['impresoras-y-escaneres/impresora-tinta', PRINTER],
            ['memorias/memorias-ram-pc/', RAM],
            ['memorias/memoria-flash', MEMORY_CARD],
            ['memorias/pendrive', USB_FLASH_DRIVE],
            ['monitores-y-proyectores/monitor', MONITOR],
            ['smart-tv', TELEVISION]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 25:
                    raise Exception('page overflows: ' + url_extension)
                url_webpage = 'https://soluservi.cl/categoria/{}/' \
                              '?product-page={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('ul', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('li', 'product'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls
