import logging

from bs4 import BeautifulSoup

from storescraper.categories import EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, \
    SOLID_STATE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, RAM, MONITOR, NOTEBOOK, \
    KEYBOARD, MOUSE, HEADPHONES, MOTHERBOARD, PROCESSOR, CPU_COOLER, VIDEO_CARD
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class NatCom(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            NOTEBOOK,
            KEYBOARD,
            MOUSE,
            HEADPHONES,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_CARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['disco-duro-externo', EXTERNAL_STORAGE_DRIVE],
            ['discos-duros', STORAGE_DRIVE],
            ['discos-ssd', SOLID_STATE_DRIVE],
            ['certificada', POWER_SUPPLY],
            ['no-certificada', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['ram-pc-escritorio', RAM],
            ['ram-portatiles', RAM],
            ['monitores', MONITOR],
            ['notebooks', NOTEBOOK],
            ['teclados', KEYBOARD],
            ['mouse', MOUSE],
            ['audifonos', HEADPHONES],
            ['placa-madre-amd', MOTHERBOARD],
            ['placa-madre-intel', MOTHERBOARD],
            ['procesadores-amd', PROCESSOR],
            ['procesadores-intel', PROCESSOR],
            ['refrigeracion-liquida', CPU_COOLER],
            ['ventiladores', CPU_COOLER],
            ['tarjetas-de-video-amd', VIDEO_CARD],
            ['tarjetas-de-video-nvidia', VIDEO_CARD],

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
                url_webpage = 'https://natcomchile.cl/{}/page/{}/'.format(
                    url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll()
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
        pass
