import re

import demjson
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Carrefour(Store):
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
            ['electrohogar-1/heladeras-freezers.html', 'Refrigerator'],
            ['climatizacion/aire-acondicionado/split-frio-calor.html',
             'AirConditioner'],
            ['electrohogar-1/calefones.html', 'WaterHeater'],
            ['electrohogar-1/lavado-y-secado/lavarropas.html',
             'WashingMachine'],
            ['electrohogar-1/cocinas-y-purificadores.html?cat=460',
             'Stove'],  # Cocinas a gas
            # ['electrohogar-1/cocinas-y-purificadores.html?cat=461',
            #  'Stove'],  # Cocinas electricas
            ['electrohogar-1/hornos-y-anafes.html',
             'Stove'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            separator = '?'

            if '?' in category_path:
                separator = '&'

            category_url = 'https://www.carrefour.com.ar/{}{}limit=all'.format(
                    category_path, separator)

            soup = BeautifulSoup(
                session.get(category_url, verify=False).text, 'html.parser')
            containers = soup.find('ul', 'products-grid').findAll(
                'li', 'item')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url, verify=False).text
        soup = BeautifulSoup(page_source, 'html.parser')

        pricing_text = re.search(
            r'var productDetail = ([\S\s]+?);', page_source)
        pricing_json = demjson.decode(pricing_text.groups()[0])

        name = pricing_json['name']
        sku = pricing_json['id']

        normal_price = Decimal(pricing_json['price'])
        offer_price = normal_price

        descriptions = [html_to_markdown(str(tag))
                        for tag in soup.findAll('div', 'tab-container')]
        description = '\n\n'.join(descriptions)

        picture_urls = [tag['src'] for tag in
                        soup.findAll('img', 'gallery-image')[1:]]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            normal_price,
            offer_price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
