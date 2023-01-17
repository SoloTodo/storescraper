from decimal import Decimal
import demjson
import logging
from bs4 import BeautifulSoup
from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import *
from storescraper.utils import session_with_proxy


class DigitalChoice(Store):
    @classmethod
    def categories(cls):
        return [
            USB_FLASH_DRIVE,
            HEADPHONES,
            MONITOR,
            MOUSE,
            KEYBOARD,
            MICROPHONE,
            STEREO_SYSTEM,
            KEYBOARD_MOUSE_COMBO
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento', USB_FLASH_DRIVE],
            ['audifonos', HEADPHONES],
            ['parlantes', STEREO_SYSTEM],
            ['microfonos', MICROPHONE],
            ['mouse', MOUSE],
            ['teclados', KEYBOARD],
            ['kit-teclado-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['monitores', MONITOR],
            ['2da-seleccion', MONITOR],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://digitalchoice.cl/collection/{}?' \
                'limit=1000'.format(url_extension)
            print(url_webpage)
            response = session.get(url_webpage)

            data = response.text
            soup = BeautifulSoup(data, 'html5lib')
            product_containers = soup.findAll('section', 'grid__item')

            if len(product_containers) == 0:
                logging.warning('Empty category: ' + url_extension)

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(
                    'https://digitalchoice.cl' + product_url)
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
            json_data = demjson.decode(product_script.text)

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

            if 'open box' in name.lower():
                condition = "https://schema.org/RefurbishedCondition"
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
