import json
import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, CELL, MOTHERBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class SmartDeal(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            CELL,
            MOTHERBOARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('computacion', NOTEBOOK),
            ('smartphones-y-tablets', CELL),
            ('componentes-y-otros', MOTHERBOARD),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if category != local_category:
                continue

            page = 1

            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + category_path)

                page_url = 'https://smartdeal.cl/categoria-producto/{}/' \
                           '?product-page={}'.format(category_path, page)
                print(page_url)
                response = session.get(page_url)
                data = response.text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + category_path)
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        sku = str(product_data['sku'])
        price = Decimal(product_data['offers'][0]['price'])
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[-1]

        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        elif soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = -1

        condition_tag = soup.find('span', 'tagged_as')
        if condition_tag and condition_tag.find('a').text == 'Nuevo y Sellado':
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
