import logging
from decimal import Decimal
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, POWER_SUPPLY, PROCESSOR, \
    VIDEO_CARD, NOTEBOOK, TABLET, ALL_IN_ONE, RAM, USB_FLASH_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    KEYBOARD_MOUSE_COMBO, MONITOR, PRINTER, CELL, STEREO_SYSTEM, HEADPHONES, \
    GAMING_CHAIR, COMPUTER_CASE, KEYBOARD, MOUSE, UPS, WEARABLE, CPU_COOLER, \
    MEMORY_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


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
            GAMING_CHAIR,
            COMPUTER_CASE,
            KEYBOARD,
            MOUSE,
            UPS,
            CPU_COOLER,
            MEMORY_CARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computacion/notebooks', NOTEBOOK],
            ['computacion/ipad-tablets', TABLET],
            ['computacion/all-in-one', ALL_IN_ONE],
            ['componentes/gabinetes', COMPUTER_CASE],
            ['componentes/placas-madres', MOTHERBOARD],
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/tarjetas-de-video', VIDEO_CARD],
            ['componentes/memorias/memorias-ram', RAM],
            ['componentes/memorias/pendrive', USB_FLASH_DRIVE],
            ['componentes/memorias/tarjetas-de-memoria-flash', MEMORY_CARD],
            ['componentes/almacenamiento/discos-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['componentes/almacenamiento/discos-internos', STORAGE_DRIVE],
            ['componentes/almacenamiento/ssd', SOLID_STATE_DRIVE],
            ['perifericos/kit-teclado-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['perifericos/monitores', MONITOR],
            ['perifericos/impresion-y-scanners', PRINTER],
            ['perifericos/proteccion-electrica/ups', UPS],
            ['electronica/relojes-inteligentes', WEARABLE],
            ['electronica/celulares', CELL],
            ['electronica/parlantes', STEREO_SYSTEM],
            ['electronica/audifonos', HEADPHONES],
            ['gamer/notebook-gamer', NOTEBOOK],
            ['gamer/monitor-gamer', MONITOR],
            ['gamer/gabinetes-gamer', COMPUTER_CASE],
            ['gamer/memorias-gamer', RAM],
            ['gamer/fuentes-de-poder-gamer', POWER_SUPPLY],
            ['gamer/teclados-gamer', KEYBOARD],
            ['gamer/mouse-gamer', MOUSE],
            ['gamer/audifonos-gamer', HEADPHONES],
            ['gamer/sillas-gamer', GAMING_CHAIR],
            ['perifericos/teclados', KEYBOARD],
            ['perifericos/mouse', MOUSE],
            ['componentes/enfriamiento-y-ventilacion', CPU_COOLER]
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            local_product_urls = []
            done = False
            page = 1
            while True:
                url_webpage = 'https://globalbox.cl/{}?p={}'.format(
                    url_extension, page)
                print(url_webpage)

                if page > 10:
                    raise Exception('page overflow: ' + url_webpage)

                response = session.get(url_webpage, verify=False)

                if response.url != url_webpage:
                    raise Exception(
                        'URL mismatch: {} {}'.format(
                            url_webpage, response.url))

                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'item isotope-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in local_product_urls:
                        done = True
                        break
                    local_product_urls.append(product_url)

                if done:
                    product_urls.extend(local_product_urls)
                    break

                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', {'itemprop': 'name'}).text
        key = soup.find('input', {'name': 'product'})['value']
        sku = soup.find('th', text='SKU').parent.find('td').text.strip()
        part_number = soup.find('th', text='Part Number').parent.find(
            'td').text.strip()
        availability_tag = soup.find('link', {'itemprop': 'availability'})

        if not availability_tag or availability_tag['href'] != \
                'http://schema.org/InStock':
            stock = 0
        else:
            stock = -1

        price = Decimal(
            remove_words(soup.find('span', 'regular-price').text.strip()))
        picture_urls = [tag['src'] for tag in
                        soup.find('figure').findAll('img')]
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
            part_number=part_number,
            picture_urls=picture_urls
        )
        return [p]
