import json
import logging

import demjson
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class ReifStore(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Cell',
            'Tablet',
            'Headphones',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['88-portatil', 'Notebook'],
            ['85-iphone-', 'Cell'],
            ['207-ipad', 'Tablet'],
            ['127-audifonos', 'Headphones'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.reifstore.cl/{}'.format(
                category_path
            )

            response = session.get(category_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            containers = soup.findAll('div', 'product-container')

            if not containers:
                logging.warning('No products found for: ' + category_url)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        content = session.get(url).text
        soup = BeautifulSoup(content, 'html.parser')

        base_sku = soup.find('input', {'name': 'id_product'})['value']
        base_price = Decimal(
            soup.find('span', {'itemprop': 'price'})['content'])
        base_name = soup.find('h1').text.strip()
        description = html_to_markdown(
            str(soup.find('section', 'page-product-box')))

        combinations_text = re.search(r'var combinations = (.+);', content)

        if combinations_text:
            combinations = json.loads(combinations_text.groups()[0])
            products = []

            for combination_id, combination in combinations.items():
                combination_name = base_name

                for attribute in combination['attributes_values'].values():
                    combination_name += ' ' + attribute

                stock = combination['quantity']
                part_number = combination['reference']
                combination_sku = '{}_{}'.format(base_sku, combination_id)
                combination_price_delta = Decimal(combination['price'])
                combination_price = base_price + combination_price_delta

                picture_urls = [
                    'https://www.reifstore.cl/{}/product.jpg'.format(
                        combination['id_image'])
                ]

                products.append(Product(
                    combination_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    combination_sku,
                    stock,
                    combination_price,
                    combination_price,
                    'CLP',
                    sku=base_sku,
                    part_number=part_number,
                    description=description,
                    picture_urls=picture_urls
                ))

            return products
        else:
            part_number = soup.find('span', {'itemprop': 'sku'})['content']

            availability = soup.find('link', {'itemprop': 'availability'})

            if availability and \
                    availability['href'] == 'http://schema.org/InStock':
                stock = -1
            else:
                stock = 0

            picture_urls = []

            for tag in soup.find(
                    'ul', {'id': 'thumbs_list_frame'}).findAll('a'):
                picture_url = demjson.decode(
                    re.search(r'rel="(.+?)"', str(tag)).groups()[0])[
                    'largeimage']
                picture_urls.append(picture_url)

            p = Product(
                base_name,
                cls.__name__,
                category,
                url,
                url,
                base_sku,
                stock,
                base_price,
                base_price,
                'CLP',
                sku=base_sku,
                part_number=part_number,
                description=description,
                picture_urls=picture_urls
            )

            return [p]
