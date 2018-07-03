import json
import urllib

import re

import demjson
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13, \
    html_to_markdown


class Sanborns(Store):
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
            ['100301', 'MemoryCard'],
            ['100205', 'UsbFlashDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.sanborns.com.mx/categoria/' \
                           '{}/'.format(category_path)

            soup = BeautifulSoup(session.get(category_url).text,
                                 'html.parser')

            link_containers = soup.findAll('article', 'productbox')

            if not link_containers:
                raise Exception('Empty category: ' + category_url)

            for link_container in link_containers:
                product_url = 'https://www.sanborns.com.mx' + \
                              link_container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        skus = soup.findAll('div', 'skuTienda')
        sku = skus[0].text.replace('SKU#. ', '').strip()
        ean = skus[1].text.replace('EAN#. ', '').strip()

        if len(ean) == 12:
            ean = '0' + ean
        if not check_ean13(ean):
            ean = None

        pricing_str = re.search(r'dataLayer = ([\S\s]+?);',
                                page_source).groups()[0]
        pricing_data = demjson.decode(pricing_str)[0]

        json_product = pricing_data['ecommerce']['detail']['products'][0]

        name = '{} {}'.format(json_product['brand'], json_product['name'])
        price = Decimal(json_product['price'])

        picture_urls = [soup.find('img', 'tienda_Detalle')['src']]

        specs_table = soup.find('dl', 'descTable')
        description = html_to_markdown(str(specs_table))
        part_number = None

        for idx, header in enumerate(specs_table.findAll('dt')):
            if header.text.lower().strip() == 'modelo':
                part_number = specs_table.findAll('dd')[idx].text.strip()
                break

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

        return [p]
