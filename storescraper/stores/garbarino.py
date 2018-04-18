import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Garbarino(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'AirConditioner',
            'WaterHeater',
            'WashingMachine',
            'Stove',
            'UsbFlashDrive',
            'MemoryCard',
            'ExternalStorageDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['heladeras-con-freezer/4296', 'Refrigerator'],
            ['heladeras-sin-freezer/4291', 'Refrigerator'],
            ['freezers/4292', 'Refrigerator'],
            ['aires-acondicionados-split/4278', 'AirConditioner'],
            ['calefones/4251', 'WaterHeater'],
            ['lavarropas/4298', 'WashingMachine'],
            ['lavasecarropas/4300', 'WashingMachine'],
            ['cocinas/4282', 'Stove'],
            ['anafes/4286', 'Stove'],
            ['hornos/4283', 'Stove'],
            ['pendrives/4553', 'UsbFlashDrive'],
            ['accesorios-fotografia/4357', 'MemoryCard'],
            ['memorias/4938', 'MemoryCard'],
            ['memorias/4935', 'MemoryCard'],
            ['discos-rigidos-externos/4549', 'ExternalStorageDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                print(category_path, page)

                category_url = 'https://www.garbarino.com/productos/{}?' \
                               'page={}'.format(category_path, page)

                page_source = session.get(category_url).text
                page_source = re.search(r'(<ul class="gb-list-grid">[\s\S]*)',
                                        page_source)

                if not page_source:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                soup = BeautifulSoup(page_source.groups()[0], 'html.parser')
                containers = soup.findAll('div', 'gb-list-cluster')

                for container in containers:
                    product_url = 'https://www.garbarino.com' + \
                          container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text

        soup = BeautifulSoup(page_source, 'html.parser')

        panel_classes = ['gb-description', 'gb-tech-spec']
        description = ''

        for panel_class in panel_classes:
            description += html_to_markdown(
                str(soup.find('div', panel_class))) + '\n\n'

        picture_urls = []
        for picture_tag in soup.findAll('li', 'gb-js-popup-thumbnail'):
            picture_url = picture_tag.find('a')['href']
            if 'youtube' in picture_url:
                continue
            picture_urls.append('https:' + picture_url)

        pricing_data = json.loads(re.search(
            r'dataLayer = ([\S\s]+?);', page_source).groups()[0])
        pricing_data = pricing_data[0]['ecommerce']['detail']['products']

        products = []

        for product_json in pricing_data:
            name = product_json['name']
            sku = product_json['id']
            price = Decimal(product_json['price'])

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
                'ARS',
                sku=sku,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
