import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words


class ProMovil(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['6-smartphones', 'Cell'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.promovil.cl/{}?n=250'.format(
                category_path)

            print(category_url)

            response = session.get(category_url)

            if response.url != category_url:
                raise Exception('Empty category: ' + category_url)

            soup = BeautifulSoup(response.text, 'html.parser')

            products_containers = soup.findAll('div', 'ajax_block_product')

            for product_container in products_containers:
                product_url = product_container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text
        sku = soup.find('input', {'name': 'id_product'})['value']

        offer_price = Decimal(remove_words(
            soup.find('span', {'id': 'our_price_display'}).text))

        normal_price_container = soup.find(
            'span', {'id': 'unit_price_display'})

        if normal_price_container:
            normal_price = Decimal(remove_words(normal_price_container.text))
            if normal_price < offer_price:
                normal_price = offer_price
        else:
            normal_price = offer_price

        stock_container = soup.find('span', {'id': 'availability_value'})

        if 'disponible' in stock_container.text.lower():
            stock = -1
        else:
            stock = 0

        description = html_to_markdown(
            str(soup.find('div', 'pb-center-column')))

        picture_urls = [tag['href'] for tag in soup.findAll('a', 'fancybox')]

        variants = re.search(r'attributesCombinations=(\[.*?\])', page_source)
        variants = json.loads(variants.groups()[0])

        if not variants:
            return [Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                normal_price,
                offer_price,
                'CLP',
                sku=sku,
                description=description,
                picture_urls=picture_urls,
            )]

        products = []

        for variant in variants:
            variant_id = variant['id_attribute']
            variant_label = variant['attribute']
            variant_field = variant['group']

            if variant_field != 'color':
                raise Exception('invalid variant')

            variant_url = '{}#/{}-{}-{}'.format(url, variant_id,
                                                variant_field, variant_label)
            variant_name = '{} - {} {}'.format(name, variant_field,
                                               variant_label)

            variant_key = '{} {}'.format(sku, variant_id)

            products.append(Product(
                variant_name,
                cls.__name__,
                category,
                variant_url,
                url,
                variant_key,
                stock,
                normal_price,
                offer_price,
                'CLP',
                sku=sku,
                description=description,
                picture_urls=picture_urls,
            ))

        return products
