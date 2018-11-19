import json
import urllib

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13


class Fravega(Store):
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
            # ['C:/1000174/1000175/', 'Refrigerator'],
            # ['C:/1000174/1000179/', 'Refrigerator'],
            # ['C:/1000174/1000183/', 'Refrigerator'],
            # ['C:/1000128/1000129/1000130/', 'AirConditioner'],
            # ['C:/1000209/1000211/', 'WaterHeater'],
            # ['C:/1000190/1000191/', 'WashingMachine'],
            # ['C:/1000157/1000158/', 'Stove'],
            # ['C:/1000157/1000166/', 'Stove'],
            # ['C:/1000157/1000170/', 'Stove'],
            ['C:/1000008/1000461/1000060/', 'UsbFlashDrive'],
            ['C:/1000008/1000461/1000062/', 'MemoryCard'],
            # ['C:/1000008/1000461/1000053/', 'ExternalStorageDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + category_path)

                category_url = 'http://www.fravega.com/buscapagina?fq={}' \
                               '&PS=50&sl=f8baa798-34ca-4594-b06d-d3ba622' \
                               '39063&cc=3&sm=0&PageNumber={}'.\
                    format(urllib.parse.quote(category_path, safe=''), page)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')
                containers = soup.findAll('li')[::2]

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_path)
                    break

                for container in containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if 'https://www.fravega.com/Sistema/404' in response.url:
            return []

        page_source = response.text
        pricing_data = re.search(r'vtex.events.addData\(([\S\s]+?)\);',
                                 page_source).groups()[0]
        pricing_data = json.loads(pricing_data)

        skus_data = re.search(r'var skuJson_0 = ([\S\s]+?);',
                              page_source).groups()[0]
        skus_data = json.loads(skus_data)
        name = '{} {}'.format(pricing_data['productBrandName'],
                              pricing_data['productName'])
        price = Decimal(pricing_data['productPriceTo'])

        soup = BeautifulSoup(page_source, 'html.parser')

        picture_urls = [tag['rel'][0] for tag in
                        soup.findAll('a', {'id': 'botaoZoom'})]

        description = html_to_markdown(
            str(soup.find('article', 'fichaProducto__specs__descripcion')))

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
            sku = str(sku_data['sku'])
            stock = pricing_data['skuStocks'][sku]

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
                'ARS',
                sku=sku,
                ean=ean,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
