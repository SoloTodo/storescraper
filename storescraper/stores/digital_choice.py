import re
from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import *
from storescraper.utils import session_with_proxy
import validators


class DigitalChoice(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            HEADPHONES,
            PRINTER,
            MONITOR,
            MOUSE,
            KEYBOARD,
            GAMING_CHAIR,
            NOTEBOOK,
            TABLET,
            SOLID_STATE_DRIVE,
            RAM,
            PROCESSOR,
            MICROPHONE,
            STEREO_SYSTEM
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento-datos/discos-duros-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento-datos/pendrives', USB_FLASH_DRIVE, ],
            ['almacenamiento-datos/tarjetas-micro-sd', MEMORY_CARD],
            ['perifericos/audifonos', HEADPHONES],
            ['perifericos/impresoras', PRINTER],
            ['monitores', MONITOR],
            ['mouse-pad', MOUSE],
            ['teclados', KEYBOARD],
            ['computacion/sillas-gamer', GAMING_CHAIR],
            ['tablet/notebooks', NOTEBOOK],
            ['tableta-digitalizadora', TABLET],
            ['almacenamiento', SOLID_STATE_DRIVE],
            ['memorias-ram', RAM],
            ['procesadores', PROCESSOR],
            ['audifonos-bluetooth', HEADPHONES],
            ['microfonos', MICROPHONE],
            ['parlantes-portatiles', STEREO_SYSTEM],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 15:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://digitalchoice.cl/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)

                data = response.text
                soup = BeautifulSoup(data, 'html5lib')
                product_containers = soup.findAll('div', 'product-block')

                if len(product_containers) == 0:
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
        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)

        base_name = json_data['name'].strip()
        description = json_data['description']
        variants_match = re.search('var productInfo = (.+);', response.text)
        products = []

        if variants_match:
            variants_data = json.loads(variants_match.groups()[0])

            for variant in variants_data:
                variant_name_suffix = ' / '.join(x['value']['name'] for x in variant['values'])
                name = '{} ({})'.format(base_name, variant_name_suffix)
                key = str(variant['variant']['id'])
                stock = variant['variant']['stock']
                price = Decimal(variant['variant']['price_decimal'])

                if validators.url(variant['image']):
                    picture_urls = [variant['image']]
                else:
                    picture_urls = None

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
                    sku=key,
                    picture_urls=picture_urls,
                    description=description
                ))
        else:
            key = soup.find('meta', {'property': 'og:id'})['content']
            price = Decimal(json_data['offers']['price'])

            stock_span = soup.find('span', 'product-form-stock')
            if not stock_span or stock_span.text == "":
                stock = 0
            else:
                stock = int(stock_span.text)

            pictures_container = soup.find('div', 'product-images')
            picture_urls = []
            for i in pictures_container.findAll('img'):
                picture_urls.append(i['src'])

            products.append(Product(
                base_name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                price,
                price,
                'CLP',
                sku=key,
                picture_urls=picture_urls,
                description=description
            ))

        return products
