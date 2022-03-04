import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class PcCenterTech(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != MOUSE:
            return []

        page = 1
        session = session_with_proxy(extra_args)
        product_urls = []

        while True:
            if page >= 10:
                raise Exception('Page overflow')

            url_webpage = 'https://www.pccentertech.cl/tienda/page/{}/'.format(
                page
            )

            res = session.get(url_webpage)

            if res.status_code == 404:
                if page == 0:
                    raise Exception('Empty store')
                break

            soup = BeautifulSoup(res.text, 'html.parser')
            product_containers = soup.findAll('li', 'product')

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
        product_data = json.loads(soup.find('script', {'type': 'application/ld+json'}).text)
        name = product_data['name']
        description = product_data['description']
        sku = str(product_data['sku'])
        price = Decimal(product_data['offers'][0]['price'])
        picture_urls = [product_data['image']]
        stock_tag = soup.find('p', 'in-stock')

        if stock_tag:
            stock = int(re.search('(\d+)', stock_tag.text).groups()[0])
        else:
            stock = 0

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
