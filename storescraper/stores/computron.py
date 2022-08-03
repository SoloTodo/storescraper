import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Computron(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            TELEVISION
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow')
                url_webpage = 'https://computron.ec/brand/lg/' \
                    'page/{}/'.format(page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('empty category')
                    break
                for container in product_containers:
                    product_url = container.find(
                        'a', 'woocommerce-LoopProduct-link')['href']
                    if product_url in product_urls:
                        continue
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('div', 'product')['id'].split('-')[-1]

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        name = json_data['name']
        sku = json_data['sku']
        description = json_data['description']

        price = Decimal(json_data['offers'][0]['price'])

        if soup.find('button', {'name': 'add-to-cart'}):
            stock = -1
        else:
            stock = 0

        picture_container = soup.find(
            'figure', 'woocommerce-product-gallery__wrapper')
        picture_urls = [tag['href']
                        for tag in picture_container.findAll('a')
                        if tag['href'] != '#']

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
            'USD',
            sku=sku,
            part_number=sku,
            description=description,
            picture_urls=picture_urls
        )
        return [p]
