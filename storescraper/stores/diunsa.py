import json
import logging
import urllib
import re

from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Diunsa(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only gets LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1

        while True:
            if page > 30:
                raise Exception('Page overflow')

            url = 'https://www.diunsa.hn/buscapagina?fq=C%3a%2f1%2f&' + \
                'ft=televisores+marca+lg&PS=12&sl=47de5394-cc68-404f-' + \
                '93ee-dca7e0b26b7f&cc=12&sm=0&PageNumber={}'.format(page)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            products = soup.findAll('div', 'contentShelve')

            if not products:
                break

            for product in products:
                product_url = product.find('a')['href']
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
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

        price = Decimal(product_json['skus'][0]['bestPrice']) / Decimal(100)
        picture_urls = [
            a['zoom'] for a in soup.findAll('a', {'id': 'botaoZoom'})]

        description = html_to_markdown(
            str(soup.find('div', 'productDescription')))

        part_number = soup.find('div', 'productReference').text.strip()

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
            'HNL',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number
        )

        return [p]
