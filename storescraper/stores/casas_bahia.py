import re
import urllib

import demjson
import requests
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown


class CasasBahia(Store):
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
            ['Informatica/ComponentesePecas/HDInterno/?Filtro=C56_C68_C2781',
             'StorageDrive'],
            ['Informatica/HDExterno/?Filtro=C56_C67',
             'ExternalStorageDrive'],
            ['TelefoneseCelulares/CartoesdeMemoria/?Filtro=C38_C32',
             'MemoryCard'],
            ['Informatica/PenDrives/?Filtro=C56_C66',
             'UsbFlashDrive'],
        ]

        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 100:
                    raise Exception('Page overflow: ' + category_path)

                category_url = \
                    'http://www.casasbahia.com.br/{}&paginaAtual={}' \
                    ''.format(category_path, page)

                print(category_url)

                soup = BeautifulSoup(requests.get(category_url).text,
                                     'html.parser')

                products = soup.findAll('div', 'hproduct')

                if not products:
                    if page == 1:
                        raise Exception('Empty category: ' + category_path)
                    break

                for product in products:
                    product_url = product.find('a')

                    if 'href' not in dict(product_url.attrs):
                        continue

                    product_url = product_url['href'].split('?')[0]
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        page_source = requests.get(url).text

        pricing_data = re.search(r'var siteMetadata = ([\S\s]+?);',
                                 page_source)
        pricing_json = demjson.decode(pricing_data.groups()[0])

        name = urllib.parse.unquote(pricing_json['page']['name'])

        if 'product' not in pricing_json['page']:
            return []

        sku = pricing_json['page']['product']['idSku']
        normal_price = Decimal(pricing_json['page']['product']['salePrice'])
        offer_price = normal_price

        if pricing_json['page']['product']['StockAvailability']:
            stock = -1
        else:
            stock = 0

        soup = BeautifulSoup(page_source, 'html.parser')

        description = html_to_markdown(
            str(soup.find('div', 'detalhesProduto')))

        picture_urls = [tag['href'] for tag in
                        soup.findAll('a', {'data-id': 'linkThumb'})
                        if 'href' in tag.attrs]

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
