from decimal import Decimal
import json
import demjson
import logging
from bs4 import BeautifulSoup
from storescraper.categories import CASE_FAN, COMPUTER_CASE, \
    EXTERNAL_STORAGE_DRIVE, HEADPHONES, KEYBOARD, MICROPHONE, MONITOR, \
    MOTHERBOARD, MOUSE, NOTEBOOK, POWER_SUPPLY, PRINTER, PROCESSOR, RAM, \
    SOLID_STATE_DRIVE, STEREO_SYSTEM, STORAGE_DRIVE, USB_FLASH_DRIVE, \
    VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Nuevatec(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            RAM,
            COMPUTER_CASE,
            CASE_FAN,
            POWER_SUPPLY,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MOUSE,
            KEYBOARD,
            USB_FLASH_DRIVE,
            PRINTER,
            MICROPHONE,
            HEADPHONES,
            NOTEBOOK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['monitores', MONITOR],
            ['procesadores', PROCESSOR],
            ['placas-madres', MOTHERBOARD],
            ['memorias-ram', RAM],
            ['discos-duros', STORAGE_DRIVE],
            ['unidades-de-estado-solido-ssd', SOLID_STATE_DRIVE],
            ['tarjetas-de-video', VIDEO_CARD],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['refrigeracion', CASE_FAN],
            ['gabinetes', COMPUTER_CASE],
            ['notebook', NOTEBOOK],
            ['impresoras', PRINTER],
            ['mouses', MOUSE],
            ['teclados', KEYBOARD],
            ['almacenamiento-externo', EXTERNAL_STORAGE_DRIVE],
            ['pendrives', USB_FLASH_DRIVE],
            ['audifonos', HEADPHONES],
            ['microfonos', MICROPHONE],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.nuevatec.cl/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-grid-item')
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]

        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)
        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        sku = str(product_data['sku'])
        description = product_data['description']
        offer_price = Decimal(product_data['offers'][0]['price'])
        normal_price = (offer_price * Decimal(1.06)).quantize(0)

        qty_input = soup.find('input', 'input-text qty text')
        if qty_input:
            if qty_input['max']:
                stock = int(qty_input['max'])
            else:
                stock = -1
        else:
            if soup.find('button', 'single_add_to_cart_button'):
                stock = 1
            else:
                stock = 0

        picture_urls = []
        image_container = soup.find('div', 'product-images')
        for image in image_container.findAll('div', 'product-image-wrap'):
            picture_urls.append(image.find('img')['src'])

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
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
