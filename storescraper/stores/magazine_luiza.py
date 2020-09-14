import json
import re

import demjson
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class MagazineLuiza(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'SolidStateDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['hd-externo/informatica-e-acessorios/s/ia/iahp/',
             'ExternalStorageDrive'],
            ['ssd/informatica-e-acessorios/s/ia/ssdc/',
             'SolidStateDrive'],
            ['cartao-de-memoria/informatica-e-acessorios/s/ia/icme/',
             'MemoryCard'],
            ['pen-drive/informatica-e-acessorios/s/ia/iapd/',
             'UsbFlashDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.magazineluiza.com.br/{}?itens=200' \
                           ''.format(category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            containers = soup.findAll(
                'div', {'itemtype': 'http://schema.org/Product'}
            )

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.url != url:
            return []

        page_source = response.text

        pricing_data = re.search(r'digitalData = ([\S\s]+?); </script',
                                 page_source).groups()[0]

        for kw in ['domain', 'fullName', 'protocol', 'pathname', 'referrer']:
            for_replace = "'{}': .+".format(kw)
            pricing_data = re.sub(for_replace, '', pricing_data)

        pricing_data = demjson.decode(pricing_data)['page']['product']

        name = pricing_data['title']
        sku = pricing_data['idSku']

        if pricing_data['stockAvailability']:
            stock = -1
        else:
            stock = 0

        if 'cashPrice' in pricing_data:
            normal_price = Decimal(pricing_data['salePrice'])
            offer_price = Decimal(pricing_data['cashPrice'])
        else:
            normal_price = Decimal(0)
            offer_price = Decimal(0)

        soup = BeautifulSoup(page_source, 'html.parser')

        description = html_to_markdown(str(soup.find('div', 'description')))

        picture_urls = [tag['data-src'] for tag in
                        soup.findAll('img', 'carousel-product__item-img')]

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
