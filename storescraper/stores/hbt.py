import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words

import json


class Hbt(Store):
    @classmethod
    def categories(cls):
        return [
            'Stove',
            'Oven',
            'CellAccesory',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('samsung/hornos-y-microondas/162', 'Oven'),
            ('samsung/campanas-y-extractores/163', 'CellAccesory'),
            ('samsung/encimeras/161', 'Stove'),
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.54.0'
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            url = 'https://www.hbt.cl/tienda/electro/{}'\
                .format(category_path)

            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            items = soup.findAll('div', 'caja-producto')

            for item in items:
                product_url = item.find('a', 'produc-hover')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.54.0'
        response = session.get(url)

        data = response.text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('h1').text.strip()
        sku = re.search(r'https://www.hbt.cl/tienda/ficha/(\d+)/', url)
        sku = sku.groups()[0]

        price = Decimal(remove_words(soup.find('div', 'precioWeb').text))

        description = ''

        for box in soup.findAll('div', 'accordionContent'):
            description += html_to_markdown(str(box) + '\n\n')

        picture_urls = [tag['href'] for tag in
                        soup.findAll('a', 'foto-ficha1')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'CRC',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
