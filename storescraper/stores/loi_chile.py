import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import MONITOR, HEADPHONES, STEREO_SYSTEM, \
    MOUSE, NOTEBOOK, TABLET, GAMING_CHAIR, VIDEO_GAME_CONSOLE, GAMING_DESK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class LoiChile(Store):
    CURRENCY = 'CLP'
    IMAGE_DOMAIN = 'd660b7b9o0mxk'

    @classmethod
    def categories(cls):
        return [
            MONITOR,
            HEADPHONES,
            STEREO_SYSTEM,
            MOUSE,
            NOTEBOOK,
            TABLET,
            GAMING_CHAIR,
            VIDEO_GAME_CONSOLE,
            GAMING_DESK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['10', MONITOR],
            ['1', HEADPHONES],
            ['25', STEREO_SYSTEM],
            ['23', MOUSE],
            ['2', NOTEBOOK],
            ['17', TABLET],
            ['154', GAMING_CHAIR],
            ['207', VIDEO_GAME_CONSOLE],
            ['155', GAMING_DESK]
        ]
        session = session_with_proxy(extra_args)
        products_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://loichile.cl/index.php?ctrl=productos&' \
                          'act=productosPorCategoriaAjax'
            payload = {'categ_id': url_extension}
            print(url_webpage)
            data = session.post(url_webpage, data=payload)
            products_ids = data.json()['html']
            soup = BeautifulSoup(products_ids, 'html.parser')
            product_containers = soup.findAll('li')
            if not product_containers:
                logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = container.find('a')['href']
                products_urls.append('https://loichile.cl/' + product_url)
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
