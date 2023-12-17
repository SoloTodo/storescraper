import json
import logging
import re
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, MOTHERBOARD, ALL_IN_ONE, CELL
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class SmartDeal(StoreWithUrlExtensions):
    url_extensions = [
        ('notebooks', NOTEBOOK),
        ('empresa', NOTEBOOK),
        ('gamer', NOTEBOOK),
        ('hogar', NOTEBOOK),
        ('notebooks/macdesign', NOTEBOOK),
        ('notebooks/apple', NOTEBOOK),
        ('notebooks/2-en-1/', NOTEBOOK),
        ('desktop', ALL_IN_ONE),
        ('componentes-y-otros', MOTHERBOARD),
        ('smartphones-y-tablets', CELL),
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            if page > 20:
                raise Exception('Page overflow')

            page_url = 'https://www.smartdeal.cl/categoria-producto/{}/' \
                       '?product-page={}'.format(url_extension, page)
            print(page_url)
            response = session.get(page_url)
            data = response.text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('li', 'product')

            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
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

        if '@graph' not in json_data:
            return []

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
        description = html_to_markdown(str(soup.find('div', 'et_pb_tabs')))

        if 'PEDIDO' in description.upper():
            stock = 0
        elif soup.find('p', 'stock out-of-stock'):
            stock = 0
        elif soup.find('p', 'stock in-stock'):
            stock_text = soup.find('p', 'stock in-stock').text
            stock = int(re.search(r'(\d+)', stock_text).groups()[0])
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
