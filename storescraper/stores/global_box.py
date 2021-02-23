
import logging

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, POWER_SUPPLY, PROCESSOR, \
    VIDEO_CARD, NOTEBOOK, TABLET, ALL_IN_ONE, RAM, USB_FLASH_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    KEYBOARD_MOUSE_COMBO, MONITOR, PRINTER, CELL, STEREO_SYSTEM, HEADPHONES
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Globalbox(Store):

    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            POWER_SUPPLY,
            PROCESSOR,
            VIDEO_CARD,
            NOTEBOOK,
            TABLET,
            ALL_IN_ONE,
            RAM,
            USB_FLASH_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            KEYBOARD_MOUSE_COMBO,
            MONITOR,
            PRINTER,
            CELL,
            STEREO_SYSTEM,
            HEADPHONES,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes/placas-madres', MOTHERBOARD],
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/tarjetas-de-video', VIDEO_CARD],
            ['computacion/notebooks', NOTEBOOK],
            ['computacion/ipad-tablets', TABLET],
            ['computacion/all-in-one', ALL_IN_ONE],
            ['componentes/memorias-ram', RAM],
            ['componentes/pendrive', USB_FLASH_DRIVE],
            ['componentes/almacenamiento/discos-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['componentes/almacenamiento/discos-internos', STORAGE_DRIVE],
            ['componentes/almacenamiento/ssd', SOLID_STATE_DRIVE],
            ['perifericos/kit-teclado-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['perifericos/monitores', MONITOR],
            ['perifericos/impresion-y-scanners', PRINTER],
            ['electronica/celulares', CELL],
            ['electronica/parlantes', STEREO_SYSTEM],
            ['electronica/audifonos', HEADPHONES],
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://globalbox.cl/{}?p={}'.format(
                    url_extension, page)
                data = session.get(url_webpage,verify=False).text
                soup = BeautifulSoup(data, 'html.parser')
                import ipdb
                ipdb.set_trace()
                product_containers = soup.findAll('li','item isotope-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty cageory: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls
