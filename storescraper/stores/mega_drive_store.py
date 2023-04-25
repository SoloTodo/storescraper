import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import EXTERNAL_STORAGE_DRIVE, MOUSE, \
    SOLID_STATE_DRIVE, USB_FLASH_DRIVE, VIDEO_CARD, PROCESSOR, MOTHERBOARD, \
    STORAGE_DRIVE, RAM, POWER_SUPPLY, CPU_COOLER, COMPUTER_CASE, KEYBOARD, \
    HEADPHONES, NOTEBOOK, MONITOR, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class MegaDriveStore(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_CARD,
            PROCESSOR,
            MOTHERBOARD,
            STORAGE_DRIVE,
            RAM,
            POWER_SUPPLY,
            CPU_COOLER,
            COMPUTER_CASE,
            KEYBOARD,
            HEADPHONES,
            NOTEBOOK,
            MONITOR,
            CASE_FAN,
            USB_FLASH_DRIVE,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MOUSE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['59-tarjetas-graficas', VIDEO_CARD],
            ['77-disco-ssd', SOLID_STATE_DRIVE],
            ['78-discos-hdd', STORAGE_DRIVE],
            ['79-discos-externos-y-cofres', EXTERNAL_STORAGE_DRIVE],
            ['80-memorias', RAM],
            ['84-usb-flah', USB_FLASH_DRIVE],
            ['85-fuentes-de-poder', POWER_SUPPLY],
            ['89-refrigeracion-liquida', CPU_COOLER],
            ['90-refrigeracion-por-aire', CPU_COOLER],
            ['92-ventiladores', CASE_FAN],
            ['94-gabinetes', COMPUTER_CASE],
            ['99-mouse', MOUSE],
            ['101-teclados', KEYBOARD],
            ['105-notebook', NOTEBOOK],
            ['110-monitores', MONITOR],
            ['112-audifonos', HEADPHONES],
            ['122-placas-madres-amd', MOTHERBOARD],
            ['123-placas-madres-intel', MOTHERBOARD],
            ['124-procesadores-amd', PROCESSOR],
            ['125-procesadores-intel', PROCESSOR],
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://megadrivestore.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find(
                    'section', {'id': 'products'}).findAll('article')
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
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(
            soup.find('div', {'id': 'product-details'})['data-product'])

        key = str(json_data['id_product'])
        name = json_data['name']
        description = html_to_markdown(json_data['description'])
        stock = json_data['quantity']
        offer_price = Decimal(json_data['price_amount'])
        normal_price = (offer_price / Decimal('0.95')).quantize(0)
        picture_urls = [i['large']['url'] for i in json_data['images']]

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
            sku=key,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
