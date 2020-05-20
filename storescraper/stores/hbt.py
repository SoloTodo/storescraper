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
            ('electrodomesticos/hornos-y-microondas/microondas', 'Oven'),
            ('electrodomesticos/hornos-y-microondas/hornos', 'Oven'),
            ('electrodomesticos/encimeras/vitroelectrica', 'Stove'),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            url = 'https://www.hbt.cl/productos/{}'\
                .format(category_path)

            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            item_container = soup.find('ul', 'itemgrid')
            items = item_container.findAll('li', 'item')

            for item in items:
                product_url = item.find('a')['href']
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
        sku = soup.find('div', 'sku').text.strip()

        price_container = soup.find('p', 'special-price')
        if not price_container:
            price_container = soup.find('span', 'regular-price')

        price = Decimal(remove_words(price_container.find(
            'span', 'price').text))
        description = html_to_markdown(str(soup.find('div', 'p-text')))

        gallery = soup.find('div', {'id': 'amasty_gallery'})
        if not gallery:
            gallery = soup.find('div', 'product-image')

        picture_urls = [i['src'].strip() for i in
                        gallery.findAll('img')]

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
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
