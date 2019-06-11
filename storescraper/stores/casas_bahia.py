import re
import urllib

import demjson
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class CasasBahia(Store):
    preferred_discover_urls_concurrency = 3
    preferred_products_for_url_concurrency = 3

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
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        session.headers['Accept-Language'] = \
            'en-US,en;q=0.9,es;q=0.8,pt;q=0.7,pt-BR;q=0.6'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 120:
                    raise Exception('Page overflow: ' + category_path)

                category_url = \
                    'https://www.casasbahia.com.br/{}&paginaAtual={}' \
                    ''.format(category_path, page)

                soup = BeautifulSoup(session.get(
                    category_url, timeout=30).text, 'html.parser')

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
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        session.headers['Accept-Language'] = \
            'en-US,en;q=0.9,es;q=0.8,pt;q=0.7,pt-BR;q=0.6'
        page_source = session.get(url, timeout=30).text

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

        picture_urls = [tag['href'].replace('\xa0', '') for tag in
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
