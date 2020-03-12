import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class SupermexDigital(Store):
    @classmethod
    def categories(cls):
        return [
            # 'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            'CpuCooler',
            'Ram',
            'VideoCard',
            'PowerSupply',
            'ComputerCase',
            # 'Ups',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Monitor',
            # 'Headphones',
            'Tablet',
            'Notebook',
            # 'Printer',
            # 'AllInOne',
            'VideoGameConsole'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento-interno/disco-mecanico', 'StorageDrive'],
            ['almacenamiento-interno/disco-solido', 'SolidStateDrive'],
            ['almacenamiento-interno/m2', 'SolidStateDrive'],
            ['tarjetas-madre', 'Motherboard'],
            ['procesadores', 'Processor'],
            ['sistema-de-enfriamiento', 'CpuCooler'],
            ['memoria-ram', 'Ram'],
            ['tarjeta-de-video', 'VideoCard'],
            ['fuente', 'PowerSupply'],
            ['gabinetes', 'ComputerCase'],
            ['mouse', 'Mouse'],
            ['teclados', 'Keyboard'],
            ['monitores', 'Monitor'],
            ['tablet', 'Tablet'],
            ['laptop', 'Notebook'],
            ['impresoras', 'Printer'],
            ['computadoras', 'AllInOne']

        ]

        base_url = 'https://www.supermexdigital.mx/collections/{}?page={}'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension, page)

                if page >= 15:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                product_container = soup.find('div',  'productgrid--items')
                products = product_container.findAll('div', 'productitem')

                if not products:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                for product in products:
                    product_url = 'https://www.supermexdigital.mx{}'\
                        .format(product.find('a')['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        data = json.loads(
            soup.find('script', {'data-section-id': 'static-product'}).text)

        variants = data['product']['variants']

        picture_urls = soup.findAll('figure', 'product-gallery--image')
        picture_urls = ['https:{}'.format(i.find('img')['src'])
                        for i in picture_urls]
        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

        products = []

        for product in variants:
            name = product['name']
            sku = product['sku']
            stock = product['inventory_quantity']
            price = Decimal(product['price']/100)

            products.append(
                Product(
                    name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    sku,
                    stock,
                    price,
                    price,
                    'MXN',
                    sku=sku,
                    picture_urls=picture_urls,
                    description=description,
                )
            )

        return products
