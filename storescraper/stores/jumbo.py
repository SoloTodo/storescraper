import json
import re
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13


class Jumbo(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Refrigerator',
            'WashingMachine',
            'Oven',
            'Printer',
            'MemoryCard',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'Headphones',
            'StereoSystem',
            'Television',
            'Mouse'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['C:/298/302/300/', 'Cell'],
            ['C:/298/302/308/', 'MemoryCard'],
            ['C:/298/302/310/', 'Headphones'],
            ['C:/298/302/309/', 'Mouse'],
            ['C:/298/302/304/', 'Mouse'],
            ['C:/298/302/305/', 'Printer'],
            ['C:/298/303/311/', 'StereoSystem'],
            ['C:/298/303/312/', 'StereoSystem'],
            ['C:/298/303/431/', 'Television'],
            ['C:/298/320/444/', 'Oven'],
            ['C:/298/320/334/', 'WashingMachine'],
            ['C:/298/320/333/', 'Refrigerator'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + url_extension)

                url_webpage = 'https://nuevo.jumbo.cl/buscapagina?sl=3a356ef' \
                              '2-a2d4-4f1b-865f-c79b6fcf0f2a&PS=18&cc=18&sm=' \
                              '0&PageNumber={}&fq={}'.format(
                                page,
                                urllib.parse.quote(url_extension, safe=''))

                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html5lib')

                product_containers = soup.findAll('div', 'product-item')

                if not product_containers:
                    if page == 0:
                        raise Exception('Empty category: ' + url_webpage)
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)

        session = session_with_proxy(extra_args)
        page_source = session.get(url).text

        pricing_data = re.search(r'vtex.events.addData\(([\S\s]+?)\);',
                                 page_source).groups()[0]
        pricing_data = json.loads(pricing_data)

        skus_data = re.search(r'var skuJson_0 = ([\S\s]+?);',
                              page_source).groups()[0]
        skus_data = json.loads(skus_data)
        name = '{} {}'.format(pricing_data['productBrandName'],
                              pricing_data['productName'])
        price = Decimal(pricing_data['productPriceTo'])
        sku = pricing_data['productReferenceId']

        soup = BeautifulSoup(page_source, 'html.parser')

        picture_urls = []

        for tag in soup.findAll('a', {'id': 'botaoZoom'}):
            picture_url = tag['zoom'] or tag['rel'][0]
            picture_urls.append(picture_url)

        products = []

        if 'productEans' in pricing_data:
            ean = pricing_data['productEans'][0]
            if len(ean) == 12:
                ean = '0' + ean
            if not check_ean13(ean):
                ean = None
        else:
            ean = None

        for sku_data in skus_data['skus']:
            key = str(sku_data['sku'])
            stock = pricing_data['skuStocks'][key]

            p = Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                ean=ean,
                description=None,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
