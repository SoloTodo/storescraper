import logging

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, PROCESSOR, VIDEO_CARD, \
    SOLID_STATE_DRIVE, STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, RAM, \
    POWER_SUPPLY, COMPUTER_CASE, CPU_COOLER, HEADPHONES, MONITOR, MOUSE, \
    STEREO_SYSTEM, KEYBOARD
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TecnoMaster(Store):
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
            KEYBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['placas-madres', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['sdd', SOLID_STATE_DRIVE],
            ['hdd', STORAGE_DRIVE],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['memorias-ram', RAM],
            ['www-tecno-master-cl-fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['refrigeracion-ventiladores', CPU_COOLER],
            ['audifonos', HEADPHONES],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['parlantes', STEREO_SYSTEM],
            ['teclados', KEYBOARD]
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
                #TODO Page number
                url_webpage = 'https://tecno-master.cl/{}/'.format(
                    url_extension)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                import ipdb
                product_containers = soup.find('div', 'thunk-content-wrap')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('li'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
                return product_urls
