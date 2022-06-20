from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import CASE_FAN, COMPUTER_CASE, CPU_COOLER, \
    GAMING_CHAIR, HEADPHONES, KEYBOARD, MONITOR, MOTHERBOARD, MOUSE, \
    NOTEBOOK, POWER_SUPPLY, PROCESSOR, RAM, SOLID_STATE_DRIVE, STORAGE_DRIVE, \
    VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Vist(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            CASE_FAN,
            VIDEO_CARD,
            MONITOR,
            NOTEBOOK,
            MOUSE,
            KEYBOARD,
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes/almacenamiento/discos-duros', STORAGE_DRIVE],
            ['componentes/almacenamiento/m-2', SOLID_STATE_DRIVE],
            ['componentes/almacenamiento/nvme', SOLID_STATE_DRIVE],
            ['componentes/almacenamiento/sata-ssd', SOLID_STATE_DRIVE],
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['componentes/gabinetes', COMPUTER_CASE],
            ['componentes/ram', RAM],
            ['componentes/placas-madre', MOTHERBOARD],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/refrigeracion/refrigeracion-liquida', CPU_COOLER],
            ['componentes/refrigeracion/cooler', CPU_COOLER],
            ['componentes/refrigeracion/fan', CASE_FAN],
            ['componentes/gpu', VIDEO_CARD],
            ['monitores', MONITOR],
            ['notebooks', NOTEBOOK],
            ['perifericos/audifonos', HEADPHONES],
            ['perifericos/mouse', MOUSE],
            ['perifericos/teclados', KEYBOARD],
            ['sillas-y-escritorios', GAMING_CHAIR],
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
                url_webpage = 'https://www.vist.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product')
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
        normal_price = (offer_price * Decimal(1.035)).quantize(0)

        input_qty = soup.find('input', 'qty')
        if input_qty:
            if 'max' in input_qty.attrs and input_qty['max']:
                stock = int(input_qty['max'])
            else:
                stock = -1
        else:
            stock = 0

        picture_urls = []
        for image in soup.findAll('div', 'woocommerce-product-gallery__image'):
            href = image.find('a')['href']
            if href != '':
                picture_urls.append(href)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
