import json

import requests
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown


class LiderBlackFriday(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'HomeTheater',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'VideoGameConsole',
            'AllInOne',
            'Projector',
            'SpaceHeater',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        return ['http://blackfriday.lider.cl/']

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        categories_dict = {
            'Computaci\xf3n': 'Notebook',
            'Smartphones': 'Cell',
            'Linea Blanca': 'Refrigerator',
            'Electrodom\xe9sticos': 'Oven',
            'Televisi\xf3n': 'Television',
            'Audio': 'StereoSystem',
            'Impresoras': 'Printer'
        }

        categories = json.loads(
            requests.get(
                'http://blackfriday.lider.cl/categories.json').text)

        product_to_type = {}

        for value in categories.values():
            for category_children in value['children']:
                for local_category, category_values in \
                        category_children.items():
                    product_type = categories_dict.get(local_category)

                    if not product_type:
                        continue

                    for producto in category_values['productos']:
                        product_to_type[producto] = product_type

        json_products = json.loads(
            requests.get(
                'http://blackfriday.lider.cl/products.json').text)['products']

        products = []

        for json_product in json_products:
            product_type = product_to_type.get(json_product['ID'])
            if product_type != category:
                continue

            product_url = 'http://blackfriday.lider.cl/#!/index.html/' \
                          + json_product['ID']

            brand = json_product['brand']
            model = json_product['displayName']
            name = u'{} {}'.format(brand, model)
            sku = json_product['sku']

            normal_price = Decimal(json_product['price']['BasePriceSales'])
            offer_price = json_product['price']['BasePriceTLMC']

            if offer_price:
                offer_price = Decimal(offer_price)
            else:
                offer_price = normal_price

            description = html_to_markdown(json_product['longDescription'])

            soup = BeautifulSoup(json_product['longDescription'],
                                 'html.parser')

            picture_urls = [tag['src'] for tag in soup.findAll('img')]

            p = Product(
                name,
                cls.__name__,
                category,
                product_url,
                url,
                sku,
                -1,
                normal_price,
                offer_price,
                'CLP',
                sku=sku,
                description=description,
                picture_urls=picture_urls
            )

            products.append(p)

        return products
