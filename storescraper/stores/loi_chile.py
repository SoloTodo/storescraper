import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import MONITOR, HEADPHONES, STEREO_SYSTEM, \
    MOUSE, NOTEBOOK, TABLET, GAMING_CHAIR, VIDEO_GAME_CONSOLE, GAMING_DESK, \
    CELL, COMPUTER_CASE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class LoiChile(StoreWithUrlExtensions):
    CURRENCY = 'CLP'
    IMAGE_DOMAIN = 'd660b7b9o0mxk'

    # URL Extensions are in a input with name "categ_id" in category pages
    url_extensions = [
        ['16', CELL],
        ['17', TABLET],
        ['10', MONITOR],
        ['1', HEADPHONES],
        ['25', STEREO_SYSTEM],
        ['2', NOTEBOOK],
        ['23', MOUSE],
        ['208', COMPUTER_CASE],
        ['207', VIDEO_GAME_CONSOLE],
        ['154', GAMING_CHAIR],
        ['155', GAMING_DESK],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        products_urls = []
        page_size = 50
        page = 0

        while True:
            if page > 10:
                raise Exception('Page overflow')
            url_webpage = ('https://loichile.cl/index.php?ctrl=productos&'
                           'act=categoriasReact&categ_id={}&cantidad={}'
                           ''.format(url_extension, page * page_size))
            print(url_webpage)
            response = session.get(url_webpage)
            product_entries = response.json()['listaProductos']

            if not product_entries:
                if page == 0:
                    logging.warning('Empty category: ' + url_extension)
                break

            for product_entry in product_entries:
                product_path = product_entry['urlseo']
                products_urls.append('https://loichile.cl/' + product_path)
            page += 1
        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        if not soup.find('div', 'pv3-pv-loi'):
            return []

        name = soup.find('h1', 'nombre-producto-info').text.replace('\t', '') \
            .replace('\n', '')
        sku = soup.find('span', {'id': 'idProducto'}).text

        price = Decimal(soup.find(
            'div', {'id': 'contenedor_precio_detalle_producto'})
                        ['data-precio'].replace(',', '.')).quantize(0)

        picture_urls = []

        for tag in soup.find('div', 'swiper-wrapper').findAll('img'):
            if tag['src'] == "":
                continue
            picture_url = 'https://{}.cloudfront.net/_img_productos/{}'.format(
                cls.IMAGE_DOMAIN, tag['src'].split('_img_productos/')[1])
            if validators.url(picture_url):
                picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            cls.CURRENCY,
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
