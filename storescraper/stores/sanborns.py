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

            page = 1

            while True:
                category_url = 'https://www.sanborns.com.mx/_layouts/' \
                               'wpSanborns/GetProductos.aspx?idFamily={}&' \
                               'page={}'.format(category_path, page)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                link_containers = soup.findAll('div', 'producto')

                if not link_containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for link_container in link_containers:
                    product_url = link_container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        query_string = urllib.parse.urlparse(url).query
        sku = urllib.parse.parse_qs(query_string)['ean'][0]

        ean = sku
        if len(ean) == 12:
            ean = '0' + ean
        if not check_ean13(ean):
            ean = None

        page_source = session.get(url).text

        pricing_str = re.search(r'dataLayer = ([\S\s]+?);',
                                page_source).groups()[0]
        pricing_data = demjson.decode(pricing_str)[0]

        json_product = pricing_data['ecommerce']['detail']['products '][0]

        name = '{} {}'.format(json_product['brand'], json_product['name'])
        price = Decimal(json_product['price'])

        soup = BeautifulSoup(page_source, 'html.parser')
        picture_urls = ['https://www.sanborns.com.mx' + tag['href'] for tag in
                        soup.findAll('a', 'zoom')]

        specs_url = 'https://www.sanborns.com.mx/_Layouts/wpSanborns/' \
                    'Especificaciones.aspx?ean={}'.format(sku)

        specs_soup = BeautifulSoup(session.get(specs_url).text, 'html.parser')

        specs_table = specs_soup.find('table')

        description = html_to_markdown(str(specs_table))

        part_number = None

        for row in specs_table.findAll('tr'):
            label = row.find('td').text.lower().strip()
            if label == 'modelo':
                part_number = row.findAll('td')[1].text.strip()
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
