from decimal import Decimal
import json
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

        key = soup.find('meta', {'property': 'og:id'})['content']

        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)

        name = json_data['name']
        description = json_data['description']
        price = Decimal(json_data['offers']['price'])

        sku = soup.find('span', 'sku_elem').text
        if sku == "":
            sku = None
        stock_span = soup.find('span', 'product-form-stock')
        if not stock_span or stock_span.text == "":
            stock = 0
        else:
            stock = int(stock_span.text)

        pictures_container = soup.find('div', 'product-images')
        picture_urls = []
        for i in pictures_container.findAll('img'):
            picture_urls.append(i['src'])

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
            picture_urls=picture_urls,
            description=description
        )

        return [p]
