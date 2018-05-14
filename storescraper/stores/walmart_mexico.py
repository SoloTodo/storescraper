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
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = '{}WebControls/hlGetProductsByLine.ashx?linea={}' \
                           '&start=0&raw=1000' \
                           ''.format(base_url, category_path)
            print(category_url)

            data = json.loads(session.get(
                category_url, verify=False).content.decode('latin-1'))

            if not data:
                raise Exception('Empty URL: ' + category_url)

            for entry in data:
                product_path = entry['ProductUrl'].strip()

                if not product_path:
                    continue
                product_url = base_url + product_path
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        response = session.get(url)
        if response.url != url:
            return []

        sku = re.search(r'(\d+)$', url).groups()[-1]

        data_url = 'https://www.walmart.com.mx/webcontrols/' \
                   'getProductDetailSolr.ashx?upc=' + sku

        print(data_url)

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

        base_description = ', '.join(product_json['Benefits']) + '\n\n'

        products = []

        for variant in product_json['variants']:
            price = Decimal(variant['data']['Price'])

            if not price:
                price = Decimal(variant['Offerts'][0]['price'])

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

            description = base_description
            for attr_entry in variant['data']['Attributes']:
                description += '{} {} \n\n'.format(attr_entry['Name'],
                                                   attr_entry['Value'])

            description += variant['data']['Details']

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
