import json
import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, CELL, TABLET, RAM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class SmartDeal(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            CELL,
            TABLET,
            RAM,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('lenovo', NOTEBOOK),
            ('huawei', NOTEBOOK),
            ('gateway', NOTEBOOK),
            ('asus', NOTEBOOK),
            ('acer', NOTEBOOK),
            ('gigabyte', NOTEBOOK),
            ('msi', NOTEBOOK),
            ('hp', NOTEBOOK),
            ('apple', NOTEBOOK),
            ('dell', NOTEBOOK),
            ('smartphones', CELL),
            ('iphone', CELL),
            ('google', CELL),
            ('smartphones-y-tablets-lenovo', TABLET),
            ('samsung', CELL),
            ('componentes-y-otros', RAM),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if category != local_category:
                continue

            response = session.get('https://smartdeal.cl/categoria-'
                                   'producto/' + category_path)
            data = response.text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('li', 'product')

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(soup.find('script', 'rank-math-schema').text)

        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        sku = product_data['sku']
        price = Decimal(product_data['offers']['price'])
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[-1]

        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        elif soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = -1

        condition_tag = soup.find('span', 'tagged_as')
        if condition_tag and condition_tag.find('a').text == 'Nuevo Sellado':
            condition = 'https://schema.org/NewCondition'
        else:
            condition = 'https://schema.org/RefurbishedCondition'

        picture_tags = soup.findAll('img', 'iconic-woothumbs-images__image')
        picture_urls = []

        for picture_tag in picture_tags:
            if 'data-large_image' in picture_tag.attrs:
                picture_url = picture_tag['data-large_image']
            else:
                picture_url = picture_tag['src']

            if validators.url(picture_url):
                picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            condition=condition,
            part_number=sku,
            picture_urls=picture_urls
        )
        return [p]
