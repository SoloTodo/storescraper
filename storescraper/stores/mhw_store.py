import logging

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, STORAGE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, PROCESSOR, RAM, MOTHERBOARD, KEYBOARD, MOUSE, \
    KEYBOARD_MOUSE_COMBO, HEADPHONES, STEREO_SYSTEM, COMPUTER_CASE, VIDEO_CARD, \
    CPU_COOLER

from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MHWStore(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            PROCESSOR,
            RAM,
            MOTHERBOARD,
            KEYBOARD,
            MOUSE,
            KEYBOARD_MOUSE_COMBO,
            HEADPHONES,
            STEREO_SYSTEM,
            COMPUTER_CASE,
            VIDEO_CARD,
            CPU_COOLER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['8-ssd-discos-estado-solido', SOLID_STATE_DRIVE],
            ['9-hdd-disco-mecanico', STORAGE_DRIVE],
            ['42-discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['4-procesadores', PROCESSOR],
            ['5-memorias-ram', RAM],
            ['6-placas-madre', MOTHERBOARD],
            ['15-teclados', KEYBOARD],
            ['16-mouses', MOUSE],
            ['17-combos-teclado-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['19-auriculares', HEADPHONES],
            ['20-parlantes', STEREO_SYSTEM],
            ['24-gabinetes', COMPUTER_CASE],
            ['36-tarjetas-de-video', VIDEO_CARD],
            ['39-cooler-cpu', CPU_COOLER]
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
                url_webpage = 'https://www.mhwstore.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('article',
                                                  'product-miniature')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
