import json
from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.product import Product
from storescraper.categories import *
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class DigitalChoice(StoreWithUrlExtensions):
    url_extensions = [
        ['discos-externos-portatiles', EXTERNAL_STORAGE_DRIVE],
        ['pendrives', USB_FLASH_DRIVE],
        ['tarjetas-micro-sd-y-lector-de-tarjetas', MEMORY_CARD],
        ['ssd-y-hdd', SOLID_STATE_DRIVE],
        ['audifonos', HEADPHONES],
        ['parlantes', STEREO_SYSTEM],
        ['microfonos', MICROPHONE],
        ['impresoras', PRINTER],
        ['monitores', MONITOR],
        ['mouse-y-mousepads', MOUSE],
        ['procesadores', PROCESSOR],
        ['teclados', KEYBOARD],
        ['sillas-gamer', GAMING_CHAIR],
        ['tablas-digitalizadoras-y-tablets', TABLET],
        ['ups-y-baterias-externas', UPS],
        ['segunda-seleccion', MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 20:
                raise Exception('Page overflow')

            url_webpage = 'https://www.digitalchoice.cl/collection/{}?' \
                          'page={}'.format(url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)

            data = response.text
            soup = BeautifulSoup(data, 'html5lib')
            product_containers = soup.findAll('section', 'grid__item')

            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(
                    'https://digitalchoice.cl' + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        products = []
        scripts = soup.findAll(
            'script', {
                'type': 'application/ld+json',
                'data-schema': 'Product'})
        for product_script in scripts:
            json_data = json.loads(product_script.text)

            key = json_data['@id']
            name = json_data['name']
            description = json_data['description']
            sku = json_data['sku']
            picture_urls = json_data['image']
            price = Decimal(json_data['offers']['price'])

            if json_data['offers']['availability'] == \
                    "https://schema.org/InStock":
                stock = -1
            else:
                stock = 0

            if 'open box' in name.lower() or 'caja abierta' in name.lower():
                condition = "https://schema.org/OpenBoxCondition"
            else:
                condition = "https://schema.org/NewCondition"

            products.append(Product(
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
                picture_urls=picture_urls,
                description=description,
                condition=condition
            ))

        return products
