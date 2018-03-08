import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13


class WalmartArgentina(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'AirConditioner',
            'WaterHeater',
            'WashingMachine',
            'Stove',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['C:/488/', 'Refrigerator'],
            ['C:/467/', 'AirConditioner'],
            # ['C:/506/', 'WaterHeater'],
            ['C:/497/', 'WashingMachine'],
            ['C:/509/511/', 'Stove'],  # Cocina
            # ['C:/509/512/', 'Stove'],  # Anafe
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url = 'http://www.walmart.com.ar/buscapagina?sl=7eb3beac-b62d-' \
                  '4de8-89c9-ed84c3e3a9aa&PS=1000&cc=4&PageNumber=1&sm=0&' \
                  'fq={}'.format(category_path)
            print(url)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            containers = soup.findAll('a', 'prateleira__image-link')

            if not containers:
                raise Exception('Empty category: ' + url)

            for container in containers:
                product_url = container['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.url != url:
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

        description = html_to_markdown(
            str(soup.find('div', 'boxProductDescription')))

        picture_urls = [tag['zoom'].split('?')[0] for tag in
                        soup.findAll('a', {'id': 'botaoZoom'}) if tag['zoom']]
        if not picture_urls:
            picture_urls = None

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
