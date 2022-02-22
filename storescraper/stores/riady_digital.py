import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import CELL, EXTERNAL_STORAGE_DRIVE, MOUSE, \
    STEREO_SYSTEM, KEYBOARD, ALL_IN_ONE, NOTEBOOK, PRINTER, TABLET, \
    HEADPHONES, MONITOR
from storescraper.utils import session_with_proxy


class RiadyDigital(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            EXTERNAL_STORAGE_DRIVE,
            MOUSE,
            STEREO_SYSTEM,
            KEYBOARD,
            ALL_IN_ONE,
            NOTEBOOK,
            PRINTER,
            TABLET,
            HEADPHONES,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['celulares', CELL],
            ['almacenamiento/discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['componentes-para-pc/mouse', MOUSE],
            ['componentes-para-pc/mouse-gamer', MOUSE],
            ['componentes-para-pc/parlantes', STEREO_SYSTEM],
            ['componentes-para-pc/teclados', KEYBOARD],
            ['componentes-para-pc/teclados-gamer', KEYBOARD],
            ['componentes-para-pc/audifonos-gamer', HEADPHONES],
            ['componentes-para-pc/monitores', MONITOR],
            ['computacion/all-in-one', ALL_IN_ONE],
            ['computacion/notebook', NOTEBOOK],
            ['computacion/notebook-gamer', NOTEBOOK],
            ['impresion', PRINTER],
            ['tabletas', TABLET],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://riadydigital.cl/wp/' \
                              'categoria-producto/{}/page/{}/'.format(
                                url_extension, page)
                response = session.get(url_webpage, timeout=30)

                if response.status_code == 404:
                    if page == 1:
                        raise Exception('Invalid category: ' + url_extension)
                    break

                data = response.text
                soup = BeautifulSoup(data, 'html5lib')
                product_containers = soup.findAll('li', 'ast-article-post')

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[1]
        stock_tag = soup.find('input', {'name': 'quantity'})

        if stock_tag:
            if 'max' in stock_tag.attrs and stock_tag.attrs['max']:
                stock = int(stock_tag['max'])
            else:
                stock = 1
        else:
            stock = 0

        json_data = json.loads(
            soup.findAll('script', {'type': 'application/ld+json'})[-1].text)
        product_data = json_data['@graph'][1]

        name = product_data['name']
        description = product_data['description']
        price = Decimal(product_data['offers'][0]['price'])
        sku = product_data['sku']
        picture_urls = [product_data['image']]

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
            picture_urls=picture_urls,
            description=description

        )
        return [p]
