import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, \
    session_with_proxy


class MercadoTech(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Tablet',
            'Notebook',
            'StereoSystem',
            'OpticalDiskPlayer',
            'PowerSupply',
            'ComputerCase',
            'Motherboard',
            'Processor',
            'VideoCard',
            'CpuCooler',
            'Printer',
            'Ram',
            'Monitor',
            'MemoryCard',
            'Mouse',
            'Cell',
            'UsbFlashDrive',
            'Television',
            'Camera',
            'Projector',
            'AllInOne',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'VideoGameConsole',
            'Ups',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):

        category_urls = [
            ['tecnologia/partes-y-piezas/almacenamiento/discos-duros',
             'StorageDrive']
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 15:
                    raise Exception('Page overflow')

                page_url = 'https://www.mercadotech.cl/t/{}?page={}'\
                    .format(category_path, page)

                print(page_url)

                soup = BeautifulSoup(session.get(page_url).text, 'html.parser')

                product_content = soup.find('div', {'data-hook': 'homepage_products'})

                if page == 1 and not product_content:
                    raise Exception('No products for url {}'.format(page_url))

                if not product_content:
                    break

                product_containers = product_content.find('div', 'row')\
                    .findAll('div', 'col-sm-4')

                for product_container in product_containers:
                    product_url = 'https://www.mercadotech.cl{}'.format(
                        product_container.find('a')['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        data = soup.find('script', {'type': 'application/ld+json'}).text
        json_data = json.loads(data)[0]

        name = json_data['name']
        sku = json_data['sku']
        stock = 0

        if json_data['offers']['availability'] == 'InStock':
            stock = -1

        price = Decimal(json_data['offers']['price'])
        picture_urls = [json_data['image']]
        description = html_to_markdown(json_data['description'])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
