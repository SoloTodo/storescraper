import re
import urllib

import demjson
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13


class ExtraBrasil(Store):
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
            ['CineFoto/CartoesdeMemoria/?Filtro=C38_C32',
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
                if page >= 120:
                    raise Exception('Page overflow: ' + category_path)

                category_url = \
                    'https://buscando.extra.com.br/{}&paginaAtual={}&' \
                    'Ordenacao=precoCrescente'.format(category_path, page)

                print(category_url)

                soup = BeautifulSoup(
                    session.get(category_url, timeout=30).text, 'html.parser')

                containers = soup.findAll('div', 'hproduct')

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for container in containers:
                    product_url = container.find('a')['href']
                    product_url = product_url.split('?')[0]
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

        picture_urls = [tag['href'].replace(' ', '%20').replace('\xa0', '')
                        for tag in soup.findAll('a', {'data-id': 'linkThumb'})
                        if 'href' in tag.attrs]

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

        return [p]
