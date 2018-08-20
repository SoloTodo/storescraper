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
            # ['heladeras-con-freezer/4296', 'Refrigerator'],
            # ['heladeras-sin-freezer/4291', 'Refrigerator'],
            # ['freezers/4292', 'Refrigerator'],
            # ['aires-acondicionados-split/4278', 'AirConditioner'],
            # ['calefones/4251', 'WaterHeater'],
            # ['lavarropas/4298', 'WashingMachine'],
            # ['lavasecarropas/4300', 'WashingMachine'],
            # ['cocinas/4282', 'Stove'],
            # ['anafes/4286', 'Stove'],
            # ['hornos/4283', 'Stove'],
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

            category_url = 'https://www.garbarino.com/productos/{}' \
                           ''.format(category_path)
            print(category_url)

            page_source = session.get(category_url).text
            soup = BeautifulSoup(page_source, 'html5lib')
            containers = soup.findAll('div', 'itemBox')

            for container in containers:
                product_url = 'https://www.garbarino.com' + \
                      container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
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

        name = soup.find('h1').text.strip()
        sku = url.split('/')[-1]
        price = soup.find('meta', {'property': 'og:price:amount'})['content']
        price = Decimal(price.replace('.', '').replace(',', '.'))

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

        return [p]
