import json

import re

from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13


class WalmartMexico(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'StorageDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.walmart.com.mx/'

        category_paths = [
            ['l-accesorios-discos-duros', 'StorageDrive'],
            ['l-accesorio-usb-sd', 'UsbFlashDrive'],
            ['l-foto-accesorios-memorias-micro', 'MemoryCard'],
            ['l-foto-accesorios-memorias-sd', 'MemoryCard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = '{}WebControls/hlGetProductsByLine.ashx?linea={}' \
                           '&start=0&raw=1000' \
                           ''.format(base_url, category_path)

            data = json.loads(session.get(
                category_url, verify=False).content.decode('latin-1'))

            if not data:
                raise Exception('Empty URL: ' + category_url)

            for entry in data:
                product_url = base_url + entry['ProductUrl']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        sku = re.search(r'(\d+)$', url).groups()[-1]

        data_url = 'https://www.walmart.com.mx/webcontrols/' \
                   'getProductDetailSolr.ashx?upc=' + sku

        product_data = session.get(
            data_url, verify=False).content.decode('latin-1')
        product_json = json.loads(product_data)

        name = product_json['DisplayName']

        picture_urls = []
        for i in range(10):
            if i == 0:
                suffix = ''
            else:
                suffix = '-{}'.format(i)

            tentative_url = 'https://www.walmart.com.mx/images/products/' \
                            'img_large/{}{}l.jpg'.format(sku, suffix)
            response = session.get(tentative_url)
            if response.apparent_encoding:
                break
            picture_urls.append(tentative_url)

        products = []

        for variant in product_json['variants']:
            price = Decimal(variant['data']['Price'])

            ean = variant['upc']
            if len(ean) == 12:
                ean = '0' + ean
            if not check_ean13(ean):
                ean = None

            part_number = None
            for attr in variant['data']['Attributes']:
                if attr['Name'].lower() == 'modelo':
                    part_number = attr['Value']
                    break

            description = variant['data']['Details']

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
                'MXN',
                sku=sku,
                ean=ean,
                part_number=part_number,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
