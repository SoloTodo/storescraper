import json

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13, \
    html_to_markdown


class Saraiva(Store):
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
            ['informatica/hd-externo', 'ExternalStorageDrive'],
            ['cameras-e-acessorios/cartoes-de-memoria', 'MemoryCard'],
            ['informatica/pen-drive', 'UsbFlashDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'http://busca.saraiva.com.br/pages/{}?page={}' \
                               ''.format(category_path, page)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                containers = soup.findAll('li', 'nm-product-item')

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for container in containers:
                    product_url = 'https:' + container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text

        pricing_data = json.loads(
            re.search(r'var customData = (.+?);',
                      page_source).groups()[0])['page']['product']

        sku = str(pricing_data['id'])
        name = '{} {}'.format(pricing_data['brand'], pricing_data['name'])
        part_number = pricing_data['mpn']

        ean = pricing_data['ean']
        if len(ean) == 12:
            ean = '0' + ean
        if not check_ean13(ean):
            ean = None

        price = Decimal(pricing_data['price'])

        if pricing_data['available']:
            stock = -1
        else:
            stock = 0

        soup = BeautifulSoup(page_source, 'html.parser')
        description = html_to_markdown(
            str(soup.find('section', {'id': 'product-information'})))

        picture_urls = []
        for tag in soup.findAll('a', 'thumb-link'):
            picture_url = tag.find('img')['src'].replace('l=50', 'l=600')
            picture_urls.append(picture_url)

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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
