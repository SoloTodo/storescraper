from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import CASE_FAN, COMPUTER_CASE, KEYBOARD, \
    MICROPHONE, MOTHERBOARD, MOUSE, POWER_SUPPLY, PROCESSOR, RAM, \
    SOLID_STATE_DRIVE, STEREO_SYSTEM, STORAGE_DRIVE, VIDEO_CARD, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class ConexionDigital(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            CASE_FAN,
            VIDEO_CARD,
            MICROPHONE,
            MOUSE,
            STEREO_SYSTEM,
            KEYBOARD,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes/almacenamiento/ssd', SOLID_STATE_DRIVE],
            ['componentes/almacenamiento/hdd', STORAGE_DRIVE],
            ['componentes/fuentes-poder', POWER_SUPPLY],
            ['componentes/gabinetes', COMPUTER_CASE],
            ['componentes/ram', RAM],
            ['componentes/placas-madres', MOTHERBOARD],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/refrigeracion', CASE_FAN],
            ['componentes/tarjetas-video', VIDEO_CARD],
            ['perifericos/audifonos', HEADPHONES],
            ['perifericos/microfonos', MICROPHONE],
            ['perifericos/mouse', MOUSE],
            ['perifericos/parlantes', STEREO_SYSTEM],
            ['perifericos/teclados', KEYBOARD],
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
                url_webpage = 'https://cxd.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find(
                        'a', 'woo_catalog_media_images')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('link', {'rel': 'shortlink'})[
            'href'].split('=')[-1]
        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        name = json_data['name']
        sku = json_data['sku']
        price = Decimal(json_data['offers'][0]['price'])

        input_qty = soup.find('input', 'qty')
        stock = 0
        if input_qty:
            if 'max' in input_qty.attrs:
                stock = int(input_qty['max'])
            else:
                stock = -1

        picture_urls = []
        for container in soup.findAll('div',
                                      'woocommerce-product-gallery__image'):
            picture_urls.append(container.find('a')['href'])

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
            part_number=sku,
            picture_urls=picture_urls
        )
        return [p]


'''
https://cxd.cl/product-category/componentes/almacenamiento/ssd/
https://cxd.cl/product-category/componentes/almacenamiento/hdd/
https://cxd.cl/product-category/componentes/fuentes-poder/
https://cxd.cl/product-category/componentes/gabinetes/
https://cxd.cl/product-category/componentes/ram/
https://cxd.cl/product-category/componentes/placas-madres/
https://cxd.cl/product-category/componentes/procesadores/
https://cxd.cl/product-category/componentes/refrigeracion/
https://cxd.cl/product-category/componentes/tarjetas-video/
https://cxd.cl/product-category/perifericos/audifonos/
https://cxd.cl/product-category/perifericos/microfonos/
https://cxd.cl/product-category/perifericos/mouse/
https://cxd.cl/product-category/perifericos/parlantes/
https://cxd.cl/product-category/perifericos/teclados/
'''
