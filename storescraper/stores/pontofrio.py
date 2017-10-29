import json
import re
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13, \
    html_to_markdown


class Pontofrio(Store):
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
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = \
                    'http://www.pontofrio.com.br/{}&paginaAtual={}' \
                    ''.format(category_path, page)

                if page >= 100:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                products = soup.findAll('div', 'hproduct')

                if not products:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
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
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        pricing_data = re.search('var siteMetadata = ([\S\s]+?);',
                                 page_source).groups()[0]

        pricing_data = json.loads(pricing_data)['page']

        if 'product' not in pricing_data:
            return []

        pricing_data = pricing_data['product']

        name = urllib.parse.unquote(pricing_data['fullName'])
        sku = pricing_data['idSku']
        price = Decimal(pricing_data['salePrice'])

        if pricing_data['StockAvailability']:
            stock = -1
        else:
            stock = 0

        soup = BeautifulSoup(page_source, 'html.parser')

        ean_container = soup.find('span', 'productEan')
        if ean_container:
            ean = re.search(r'EAN (\d+)', ean_container.text).groups()[0]
            if len(ean) == 12:
                ean = '0' + ean
            if not check_ean13(ean):
                ean = None
        else:
            ean = None

        description = html_to_markdown(
            str(soup.find('div', 'detalhesProduto')))

        picture_urls = [tag.find('img')['src'] for tag in
                        soup.findAll('a', 'jqzoom')]

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

        return [p]
