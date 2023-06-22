import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Ampera(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != MOUSE:
            return []

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []
        url_webpage = 'https://ampera.cl/tienda/'
        data = session.get(url_webpage).text
        soup = BeautifulSoup(data, 'html.parser')
        product_containers = soup.findAll('li', 'product')

        for container in product_containers:
            product_url = container.find('a', 'woocommerce-Loop'
                                              'Product-link')['href']
            product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)

        if response.url != url:
            print(response.url)
            print(url)
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        if soup.find('form', 'variations_form'):
            products = []
            variations = json.loads(soup.find('form', 'variations_form')[
                'data-product_variations'])
            for product in variations:
                variation_name = name + ' - ' + product['attributes'][
                    'attribute_pa_color']
                sku = str(product['variation_id'])
                if product['max_qty'] == '':
                    stock = 0
                else:
                    stock = product['max_qty']
                price = Decimal(product['display_price'])
                picture_urls = [product['image']['url']]
                p = Product(
                    variation_name,
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
                    picture_urls=picture_urls
                )
                products.append(p)
            return products
        else:
            json_data = json.loads(
                soup.find('script', {'type': 'application/ld+json'})
                    .text)['@graph'][1]
            sku = str(json_data['sku'])
            offer = json_data['offers'][0]
            if offer['availability'] == 'http://schema.org/InStock':
                stock_tag = soup.find('p', 'stock')
                if stock_tag:
                    stock = int(stock_tag.text.split()[0])
                else:
                    return []
            else:
                stock = 0
            price = Decimal(offer['price'])
            picture_urls = [json_data['image']]
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
                picture_urls=picture_urls
            )
            return [p]
