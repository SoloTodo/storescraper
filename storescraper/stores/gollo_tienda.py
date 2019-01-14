from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy

import re
import json


class GolloTienda(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Television',
            'OpticalDiskPlayer',
            'AirConditioner',
            'Stove',
            'Oven',
            'WashingMachine',
            'Refrigerator',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('productos/telefonia/celulares', 'Cell'),
            ('productos/pantallas/led', 'Television'),
            ('productos/audio-y-video/video/reproductores',
             'OpticalDiskPlayer'),
            ('productos/hogar/ventilacion/aire-acondicionado',
             'AirConditioner'),
            ('productos/linea-blanca/cocina/de-gas', 'Stove'),
            ('productos/linea-blanca/cocina/electricas', 'Stove'),
            ('productos/hogar/peque-os-enseres/hornos-y-tostadores',
             'Oven'),
            ('productos/linea-blanca/cocina/microondas', 'Oven'),
            ('productos/linea-blanca/lavanderia/lavadoras',
             'WashingMachine'),
            ('productos/linea-blanca/refrigeracion/refrigeradoras',
             'Refrigerator'),
            ('productos/audio-y-video/audio/minicomponentes',
             'StereoSystem'),
            ('productos/audio-y-video/audio/parlantes', 'StereoSystem')
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://www.gollotienda.com/{}/page/{}.html'\
                    .format(category_path, page)

                for i in range(10):
                    response = session.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    container = soup.find('div', 'mb-category-products')
                    if container:
                        break
                else:
                    raise Exception('Could not bypass Incapsula')

                items = container.findAll('li', 'item')

                if items:
                    for item in items:
                        product_url = item.find('a')['href']

                        if product_url in product_urls:
                            done = True
                            break

                        product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        pass
