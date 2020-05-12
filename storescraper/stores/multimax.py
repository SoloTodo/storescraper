from bs4 import BeautifulSoup
from decimal import Decimal
import json
import demjson
import re

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown

from storescraper.utils import check_ean13


class Multimax(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'WashingMachine',
            'Stove',
            'AirConditioner',
            'Monitor'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('tv', 'Television'),
            ('celulares', 'Cell'),
            ('equipos-de-sonido', 'StereoSystem'),
            ('barras-de-sonido', 'StereoSystem'),
            ('bocinas', 'StereoSystem'),
            ('aires-acondicionados/Inverter', 'AirConditioner'),
            ('aires-acondicionados/Básico', 'AirConditioner'),
            ('estufas', 'Stove'),
            ('lavadoras', 'WashingMachine'),
            ('secadoras', 'WashingMachine'),
            # ('centro-de-lavado', 'WashingMachine'),
            ('refrigeradoras', 'Refrigerator'),
            ('congeladores', 'Refrigerator'),
            # ('microondas', 'Oven'),
            # ('hornos', 'Oven'),
            ('monitores', 'Monitor'),
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

                url = 'https://www.multimax.net/collections/{}?page={}'\
                    .format(category_path, page)

                print(url)

                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html5lib')

                container = soup.find('div', 'collection-products')
                items = container.findAll('article', 'item')

                if not items:
                    if page == 1:
                        raise Exception('No products for category {}'
                                        .format(category))
                    break

                for item in items:
                    if 'LG' not in item.find('div', 'vendor').text.upper():
                        continue
                    product_url = 'https://www.multimax.net{}'\
                        .format(item.find('a')['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        products = []
        json_data = demjson.decode(
            re.search(r'current: ([\s\S]*?),\n[ \t]+customerLoggedIn',
                      response.text).groups()[0])['product']

        description = html_to_markdown(json_data['description'])

        images = json_data['images']
        picture_urls = ['https:{}'.format(image.split('?')[0])
                        for image in images]

        for variant in json_data['variants']:
            name = variant['name']
            sku = variant['sku']
            barcode = variant['barcode']

            if len(barcode) == 12:
                barcode = '0' + barcode

            if not check_ean13(barcode):
                barcode = None

            stock = variant['inventory_quantity']
            price = Decimal(variant['price'])/Decimal(100)

            products.append(Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                price,
                price,
                'USD',
                sku=sku,
                ean=barcode,
                description=description,
                picture_urls=picture_urls
            ))

        return products
