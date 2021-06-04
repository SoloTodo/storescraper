import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TiendaToyotomi(Store):
    @classmethod
    def categories(cls):
        return [
            'AirConditioner',
            'Oven',
            'VacuumCleaner',
            'SpaceHeater',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['calefaccion', 'SpaceHeater'],
            ['ventilacion/aire-acondicionado', 'AirConditioner'],
            ['electro-hogar/electrodomesticos/aspiradoras', 'VacuumCleaner'],
            ['electro-hogar/electrodomesticos/hornos-electricos', 'Oven'],
            ['electro-hogar/electrodomesticos/microondas', 'Oven'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 15:
                    raise Exception('Page overflow')

                category_url = 'https://toyotomi.cl/product-category/{}/' \
                               'page/{}'.format(category_path, page)
                print(category_url)

                soup = BeautifulSoup(
                    session.get(category_url, verify=False).text,
                    'html.parser')

                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty path: {}'.format(category_url))
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(
            session.get(url, verify=False).text, 'html.parser')

        data = soup.findAll('script', {'type': 'application/ld+json'})[-1]

        json_data = json.loads(data.text)

        if '@graph' not in json_data.keys():
            return []

        json_data = json_data['@graph'][1]

        name = json_data['name']
        sku = str(json_data['sku'])

        price = Decimal(json_data['offers'][0]['price'])

        if json_data['offers'][0]['availability'] in \
                ['https://schema.org/InStock', 'http://schema.org/InStock']:
            stock = -1
        else:
            stock = 0

        description = json_data['description']

        if 'image' not in json_data.keys():
            return []

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
