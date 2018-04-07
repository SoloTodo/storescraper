import html
import urllib

import demjson
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13, \
    html_to_markdown


class WalmartBrazil(Store):
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
            ['C:6552/6593/6597/', 'StorageDrive'],
            ['C:6552/6593/6604/', 'SolidStateDrive'],
            ['C:6552/6605/6609/', 'ExternalStorageDrive'],
            ['C:6552/6605/6614/', 'UsbFlashDrive'],
            ['C:6552/6578/6582/', 'MemoryCard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_paths, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.walmart.com.br/_search?fq={}' \
                               '&PS=40&O=OrderByTopSaleDESC&PageNumber={}' \
                               ''.format(urllib.parse.quote(category_paths,
                                                            safe=''), page)
                print(category_url)

                if page >= 200:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                containers = soup.findAll('section', 'card')

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                skipped = 0

                for container in containers:
                    if container.find('p', 'warning'):
                        skipped += 1
                        continue

                    product_path = container.find('figure').parent['href']
                    product_url = 'https://www.walmart.com.br' + product_path
                    product_urls.append(product_url)

                if skipped == 40:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text

        soup = BeautifulSoup(page_source, 'html.parser')

        picture_urls = []

        for tag in soup.findAll('li', 'owl-item'):
            picture_path = tag.find('a')['data-zoom'].replace(
                ' ', '%20').strip()

            if not picture_path:
                picture_path = tag.find('a')['data-normal'].replace(
                    ' ', '%20').strip()

            if not picture_path:
                continue
            picture_url = 'https:' + picture_path
            picture_urls.append(picture_url)

        if not picture_urls:
            picture_urls = None

        pricing_data = demjson.decode(re.search(
            r'dataLayer = ([\S\s]+?);dataLayer', page_source).groups()[0])[0]

        products = []

        for product_entry in pricing_data['product']:
            name = product_entry['productName']
            sku = str(product_entry['productSku'])
            price = Decimal(product_entry['productDiscount'])

            if product_entry['productAvailable']:
                stock = -1
            else:
                stock = 0

            description = html_to_markdown(html.unescape(
                product_entry['productDescription']))

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
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
