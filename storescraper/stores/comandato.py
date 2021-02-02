import logging
import re
import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import WASHING_MACHINE


class Comandato(Store):
    @classmethod
    def categories(cls):
        return [
            WASHING_MACHINE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        if category != WASHING_MACHINE:
            return []

        url = 'https://www.comandato.com/lg?PS=200'
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        products = soup.findAll('div', 'producto')

        if not products:
            logging.warning('Empty url {}'.format(url))

        for product in products:
            product_url = product.find('a')['href']
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        data = response.text
        soup = BeautifulSoup(data, 'html.parser')

        name_container = soup.find('div', 'productDescriptionShort')

        if not name_container:
            return []

        name = name_container.text
        sku = soup.find('div', 'skuReference').text
        stock = 0
        if soup.find('link', {'itemprop': 'availability'})['href'] == \
                'http://schema.org/InStock':
            stock = -1

        pricing_data = re.search(r'vtex.events.addData\(([\S\s]+?)\);',
                                 data).groups()[0]
        pricing_data = json.loads(pricing_data)

        tax = Decimal('1.12')
        offer_price = Decimal(pricing_data['productPriceFrom'])*tax
        normal_price = Decimal(pricing_data['productListPriceFrom'])*tax

        picture_urls = [a['zoom'] for a in
                        soup.findAll('a', {'id': 'botaoZoom'})]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'caracteristicas'})))

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
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
