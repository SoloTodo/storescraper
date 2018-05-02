import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13


class OfficeMaxMexico(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['fq=C%3a%2f14%2f39%2f&O=OrderByPriceASC&PS=1000&sl=b78d2f26-'
             '69b3-4d6c-b667-7eb86fcf57c2&cc=20&sm=0&fq=specificationFilter_'
             '91:Micro+SD&fq=specificationFilter_91:SD',
             'MemoryCard'],
            ['fq=C%3a%2f14%2f39%2f&O=OrderByPriceASC&PS=1000&sl=b78d2f26-'
             '69b3-4d6c-b667-7eb86fcf57c2&cc=20&sm=0&fq=specificationFilter_'
             '91:Disco+Duro',
             'ExternalStorageDrive'],
            ['fq=C%3a%2f14%2f39%2f&O=OrderByPriceASC&PS=1000&sl=b78d2f26-'
             '69b3-4d6c-b667-7eb86fcf57c2&cc=20&sm=0&fq=specificationFilter_'
             '91:USB',
             'UsbFlashDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.officemax.com.mx/buscapagina?' + \
                           category_path
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            items = soup.findAll('div', 'product-item')

            if not items:
                raise Exception('Empty category: ' + category_url)

            for entry in items:
                product_url = entry.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text

        skus_data = re.search(r'var skuJson_0 = ([\S\s]+?);',
                              page_source).groups()[0]
        skus_data = json.loads(skus_data)
        soup = BeautifulSoup(page_source, 'html.parser')

        part_number = soup.find('td', {'class': 'value-field Modelo'}).text

        picture_urls = [tag['rel'][0].split('?')[0] for tag in
                        soup.findAll('a', {'id': 'botaoZoom'})]

        products = []

        for sku_data in skus_data['skus']:
            sku = str(sku_data['sku'])
            name = sku_data['skuname']
            price = Decimal(sku_data['bestPrice']) / Decimal(100)

            if sku_data['available']:
                stock = -1
            else:
                stock = 0

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
                'MXN',
                sku=sku,
                part_number=part_number,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
