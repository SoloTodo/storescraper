import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import TELEVISION


class Rodelag(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only interested in LG products

        session = session_with_proxy(extra_args)
        product_urls = []
        if TELEVISION != category:
            return []

        page = 1
        while True:
            if page >= 15:
                raise Exception('Page overflow')

            url = 'https://rodelag.com/collections/lg' \
                '?page={}'.format(page)
            print(url)
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html5lib')
            product_containers = soup.findAll('article', 'productitem')

            if not product_containers:
                if page == 1:
                    logging.warning('Empty category:' + url)
                break

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(
                    'https://rodelag.com' + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')

        part_number_tag = soup.find('div', 'product-part_number')
        if part_number_tag:
            part_number = part_number_tag.find('span').string.strip() or None
        else:
            part_number = None

        json_data = json.loads(soup.find(
            'script', {'data-section-id': 'static-product'}).string)
        json_product = json_data['product']

        description = html_to_markdown(json_product['description'])
        picture_urls = ['https:' + i for i in json_product['images']]

        json_data_variants = json_product['variants']
        assert len(json_data_variants) == 1

        v_data = json_data_variants[0]
        sku = v_data['sku']
        name = v_data['name']
        if v_data['available']:
            stock = -1
        else:
            stock = 0
        price = Decimal(v_data['price']) / Decimal(100)

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
            'USD',
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
