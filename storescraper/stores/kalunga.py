import json

import re

import demjson
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13


class Kalunga(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'SolidStateDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['midias-drives/hd-externo-portatil/23/1137',
             'ExternalStorageDrive'],
            ['midias-drives/memoria-ssd/23/1448', 'SolidStateDrive'],
            ['midias-drives/cartoes-de-memoria-micro-sd/23/994', 'MemoryCard'],
            ['midias-drives/pen-drive/23/614', 'UsbFlashDrive'],
            ['midias-drives/pen-drive-3-em-1/23/1380', 'UsbFlashDrive'],
            ['midias-drives/pen-drive-dual-drive/23/1377', 'UsbFlashDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.kalunga.com.br/depto/{}' \
                           ''.format(category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            containers = soup.findAll('div', 'blocoproduto')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = 'https://www.kalunga.com.br' + \
                              container.find('a')['href']
                product_url = product_url.split('?')[0]
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text

        pricing_data = demjson.decode(re.search(
            r'dataLayer = ([\S\s]+?);', page_source).groups()[0])[0]

        name = pricing_data['prodName']
        sku = str(pricing_data['prodid'][0])

        ean = pricing_data['barcode'].strip()
        if len(ean) == 12:
            ean = '0' + ean
        if not check_ean13(ean):
            ean = None

        availability = pricing_data['in_stock']

        if availability == 'Y':
            stock = -1
        else:
            stock = 0

        price = Decimal(pricing_data['totalvalue'])

        soup = BeautifulSoup(page_source, 'html.parser')

        picture_urls = [tag['src'] for tag in
                        soup.findAll('img', 'imgGallery')]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'descricaoPadrao'})))

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
            'BRL',
            sku=sku,
            ean=ean,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
