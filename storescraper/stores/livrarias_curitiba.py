import json
import urllib

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13


class LivrariasCuritiba(Store):
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
            ['C:/6/63/298/', 'UsbFlashDrive'],
            ['C:/6/61/317/', 'MemoryCard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = \
                    'http://www.livrariascuritiba.com.br/buscapagina?fq={}&' \
                    'PS=16&sl=1ac72559-0af1-49ae-bf8d-a6c48490c420&' \
                    'cc=16&sm=0&PageNumber={}&O=OrderByPriceASC' \
                    ''.format(urllib.parse.quote(category_path), page)

                if page >= 50:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                containers = soup.findAll('li', 'tecnologia')

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for container in containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
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

        soup = BeautifulSoup(page_source, 'html.parser')

        description = ''
        panel_classes = ['produto-contents--sinope',
                         'produto-contents--caracteristicas']

        for panel_class in panel_classes:
            panel = soup.find('li', panel_class)
            description = html_to_markdown(str(panel)) + '\n\n'

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

            picture_urls = [sku_data['image'].split('?')[0].replace(
                '-300-300', '')]

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
            products.append(p)

        return products
