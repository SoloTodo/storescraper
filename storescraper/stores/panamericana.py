import json
import urllib

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13


class Panamericana(Store):
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
        category_paths = [
            ['C:/88/89/96/', 'ExternalStorageDrive'],
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
                encoded_path = urllib.parse.quote(category_path, safe='')

                category_url = 'https://www.panamericana.com.co/buscapagina' \
                               '?fq={}&PS=50&sl=08b00169-85d5-41ff-a2f2-' \
                               '61e335c4fa88&cc=1&sm=0&&PageNumber={}' \
                               ''.format(encoded_path, page)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                link_containers = soup.findAll('div', 'productShelf')

                if not link_containers:
                    if page == 1:
                        raise Exception('Page overflow: ' + category_url)
                    break

                for link_container in link_containers:
                    product_url = link_container.find('a')['href']
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
        price = (Decimal(pricing_data['productPriceTo']) *
                 Decimal('1.19')).quantize(0)

        soup = BeautifulSoup(page_source, 'html.parser')

        description = html_to_markdown(
            str(soup.find('div', 'boxProductDescription')))
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

            picture_urls = [sku_data['image']]

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
                'COP',
                sku=sku,
                ean=ean,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
