import urllib
from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    GAMING_CHAIR, NOTEBOOK, OVEN, PRINTER, RAM, REFRIGERATOR, STEREO_SYSTEM,
    TELEVISION, WEARABLE, CELL, VIDEO_GAME_CONSOLE, SPACE_HEATER, HEADPHONES,
    WASHING_MACHINE)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy


class BodegaOportunidades(StoreWithUrlExtensions):
    url_extensions = [
        ['Calefacción', SPACE_HEATER],
        ['Celulares y telefonía', CELL],
        ['Computación', NOTEBOOK],
        ['Consolas y videojuegos', VIDEO_GAME_CONSOLE],
        ['Discos y accesorios', RAM],
        ['Electrónica, audio y video', STEREO_SYSTEM],
        ['Hornos y microondas', OVEN],
        ['Hornos, cocinas y encimeras', OVEN],
        ['Impresoras', PRINTER],
        ['Lavado', WASHING_MACHINE],
        ['Muebles', GAMING_CHAIR],
        ['Refrigeradores y frigobar', REFRIGERATOR],
        ['Smarwatch y Smartband', WEARABLE],
        ['Tecnología gamer', HEADPHONES],
        ['Televisores', TELEVISION],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('Page overflow: ' + url_extension)
            url_webpage = 'https://bodegaoportunidades.cl/collections/' \
                          'todos-los-productos?filter.p.product_type=' \
                          '{}&page={}'.format(
                            urllib.parse.quote(url_extension), page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div', 'product-item')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = container.find('a')['href'].split('?')[0]
                product_urls.append(
                    'https://bodegaoportunidades.cl' + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/json'})[-1].text)['product']

        description = html_to_markdown(json_data['description'])
        picture_urls = ['https:' + i for i in json_data['images']]

        products = []
        for variant in json_data['variants']:
            key = str(variant['id'])
            sku = variant['sku']
            name = variant['name']
            price = (Decimal(variant['price']) / Decimal(100)).quantize(0)

            if variant['available']:
                stock = -1
            else:
                stock = 0

            product = Product(
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
                description=description,
                condition='https://schema.org/OpenBoxCondition'
            )
            products.append(product)

        return products
