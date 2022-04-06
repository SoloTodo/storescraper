import json
import re

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import TELEVISION


class CreditosEconomicos(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1

        while True:
            if page > 30:
                raise Exception('Page overflow')

            url = 'https://www.creditoseconomicos.com/buscapagina?ft=lg&PS=' \
                  '48&sl=4d4f6591-174d-49b2-8390-3d8eebb7981f' \
                  '&cc=1&sm=0&PageNumber={}'.format(page)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            products = soup.findAll('a')

            if not products:
                if page == 1:
                    raise Exception('Empty url {}'.format(url))
                else:
                    break

            for product in products:
                product_url = product['href']
                if product_url == '#':
                    continue
                product_url += '?sc=2'

                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code != 200:
            if '?sc=2' in url:
                return cls.products_for_url(
                    url.replace('?sc=2', ''), category, extra_args)

            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        scripts = soup.findAll('script')
        product_data = [s for s in scripts if 'var skuJson' in s.text]

        if product_data:
            product_data = product_data[0].text
        else:
            raise Exception('No Data')

        product_json = json.loads(re.search(
            r'var skuJson_0 = ([\S\s]+?);', product_data).groups()[0])

        name = product_json['name']
        sku = str(product_json['skus'][0]['sku'])
        stock = 0
        if product_json['available']:
            stock = -1

        price = Decimal(product_json['skus'][0]['bestPrice'] +
                        product_json['skus'][0]['taxAsInt']) / Decimal(100)

        picture_urls = [
            a['zoom'] for a in soup.findAll('a', {'id': 'botaoZoom'})]

        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

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
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
