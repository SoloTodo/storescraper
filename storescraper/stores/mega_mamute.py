import json
import urllib

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13


class MegaMatute(Store):
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
            ['C:/164/168/170/', 'StorageDrive'],
            ['C:/164/168/169/', 'ExternalStorageDrive'],
            ['C:/164/168/172/', 'SolidStateDrive'],
            ['C:/164/168/173/', 'UsbFlashDrive'],
            ['C:/8/116/118/', 'MemoryCard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = \
                    'http://www.megamamute.com.br/buscapagina?fq={}&PS=16&' \
                    'sl=45e718bf-51b0-49c4-8882-725649af0594' \
                    '&cc=3&sm=0&PageNumber={}' \
                    ''.format(urllib.parse.quote(category_path), page)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                print(category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                containers = soup.findAll('div', 'x-product')

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for container in containers:
                    product_url = container.find('h2').find('a')['href']
                    product_urls.append(product_url)

                page += 1

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
        normal_price = Decimal(pricing_data['productPriceTo'])

        soup = BeautifulSoup(page_source, 'html.parser')

        discount_container = soup.find('div', 'price_box-v1').fetchParents()[0]
        discount_container = discount_container.findAll('p', 'flag')
        if discount_container:
            discount_container = discount_container[-1]
            discount_value = re.search(r'(\d+)', discount_container.text)
            discount_value = Decimal(discount_value.groups()[0])
            discount_factor = (Decimal(100) - discount_value) / Decimal(100)

            offer_price = normal_price * discount_factor
            offer_price = offer_price.quantize(Decimal('0.01'))
        else:
            offer_price = normal_price

        picture_urls = [tag['rel'][0].split('?')[0] for tag in
                        soup.findAll('a', {'id': 'botaoZoom'})]

        description = ''
        panel_classes = ['blc_1', 'blc_2']

        for panel_class in panel_classes:
            panel = soup.find('div', panel_class)
            description += html_to_markdown(str(panel)) + '\n\n'

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
                normal_price,
                offer_price,
                'BRL',
                sku=sku,
                ean=ean,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
