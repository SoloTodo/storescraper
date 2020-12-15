import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class TiendaSmart(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Tablet',
            'Headphones',
            'StereoSystem',
            'Wearable',
            'CellAccesory'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['3-smartphones.html', 'Cell'],
            ['tablets.html', 'Tablet'],
            ['audios/portipo/auriculares.html', 'Headphones'],
            ['wearabless.html', 'Wearable'],
            ['accesorios.html', 'CellAccesory'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                category_url = 'https://tiendasmart.cl/{}?' \
                               'p={}&product_list_limit=30' \
                    .format(category_path, page)
                print(category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')
                product_containers = soup.find(
                    'div', {'id': 'amasty-shopby-product-list'}).findAll(
                    'div', 'product-hover')

                done = False

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + category_url)
                    break

                for container in product_containers:
                    product_url = container.find(
                        'a', 'product-item-photo')['href']
                    if product_url in product_urls:
                        print(product_url)
                        done = True
                        break
                    product_urls.append(product_url)

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        if 'An error has happened' in soup.text:
            return []

        name = soup.find('h1', 'page-title').text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()

        if not soup.find('span', 'price'):
            return []

        price = Decimal(
            soup.find('span', 'price').text.replace('$', '').replace('.', ''))

        if soup.find('div', 'stock available'):
            stock = -1
        else:
            stock = 0

        if 'semi nuevo' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        description = html_to_markdown(str(
            soup.find('div', {'id': 'additional'})))

        picture_urls = [
            soup.find('div', 'gallery-placeholder').find('img')['src']]

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
            'CLP',
            sku=sku,
            part_number=sku,
            description=description,
            picture_urls=picture_urls,
            condition=condition
        )

        return [p]
