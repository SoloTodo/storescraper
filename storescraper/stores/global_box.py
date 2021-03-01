import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, POWER_SUPPLY, PROCESSOR, \
    VIDEO_CARD, NOTEBOOK, TABLET, ALL_IN_ONE, RAM, USB_FLASH_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    KEYBOARD_MOUSE_COMBO, MONITOR, PRINTER, CELL, STEREO_SYSTEM, HEADPHONES
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

            local_product_urls = []
            done = False
            page = 1
            while True:
                url_webpage = 'https://globalbox.cl/{}?p={}'.format(
                    url_extension, page)

                if page > 10:
                    raise Exception('page overflow: ' + url_webpage)

                data = session.get(url_webpage, verify=False).text
                soup = BeautifulSoup(data, 'html.parser')
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
        sku = soup.find('th', text='SKU').next.next.next.text
        part_number = soup.find('th', text='Part Number').next.next.next.text
        if soup.find('link', {'itemprop': 'availability'})[
             'href'] == 'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0
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
            sku,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls
        )
        return [p]
