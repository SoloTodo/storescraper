import html
import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, TABLET, CELL, PRINTER, \
    ALL_IN_ONE, TELEVISION, PROCESSOR, CPU_COOLER, MOTHERBOARD, HEADPHONES, \
    VIDEO_CARD, COMPUTER_CASE, RAM, POWER_SUPPLY, SOLID_STATE_DRIVE, \
    MEMORY_CARD, USB_FLASH_DRIVE, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class BookComputer(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TABLET,
            CELL,
            PRINTER,
            ALL_IN_ONE,
            TELEVISION,
            PROCESSOR,
            CPU_COOLER,
            MOTHERBOARD,
            HEADPHONES,
            VIDEO_CARD,
            COMPUTER_CASE,
            RAM,
            POWER_SUPPLY,
            SOLID_STATE_DRIVE,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebook-outlet', NOTEBOOK],
            ['computadores-y-tablets/notebooks', NOTEBOOK],
            ['tablet-outlet', TABLET],
            ['tablets-1', TABLET],
            ['celulares-outlet', CELL],
            ['outlet/impresoras', PRINTER],
            ['outlet/all-in-one', ALL_IN_ONE],
            ['all-in-one', ALL_IN_ONE],
            ['outlet/televisores', TELEVISION],
            ['componentes-1/procesador', PROCESSOR],
            ['procesadores', PROCESSOR],
            ['gamers/enfriamiento', CPU_COOLER],
            ['componentes-1/placas-madre', MOTHERBOARD],
            ['tarjeta-madre', MOTHERBOARD],
            ['gamers/perifericos', HEADPHONES],
            ['gamers/tarjetas-de-video', VIDEO_CARD],
            ['tarjeta-de-video', VIDEO_CARD],
            ['gabinetes', COMPUTER_CASE],
            ['memorias-ram', RAM],
            ['fuente-de-poder', POWER_SUPPLY],
            ['almacenamiento/ssd/hdd', SOLID_STATE_DRIVE],
            ['almacenamiento/memorias-sd', MEMORY_CARD],
            ['almacenamiento/pendrive', USB_FLASH_DRIVE],
            ['monitores', MONITOR]
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
                url_webpage = 'https://www.bookcomputer.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-block')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.bookcomputer.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_info = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        name = json_info['sku']+' - '+html.unescape(json_info['name'])
        sku = soup.find('form', 'product-form form-horizontal')[
            'action'].split('/')[-1]
        if json_info['offers']['availability'] == "http://schema.org/InStock":
            stock = int(soup.find('span', 'product-form-stock').text)
        else:
            stock = 0
        price = Decimal(json_info['offers']['price'])
        picture_urls = [json_info['image'].split('?')[0]]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
