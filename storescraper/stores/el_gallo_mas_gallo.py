import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, TELEVISION, STEREO_SYSTEM, \
    REFRIGERATOR, WASHING_MACHINE, AIR_CONDITIONER, OVEN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class ElGalloMasGallo(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 0
        while True:
            if page > 10:
                raise Exception('page overflow')

            body = json.dumps({
                "requests": [
                    {
                        "indexName": "monge_upgrade_prod_elgallo_ni_products",
                        "params": "facetFilters=%5B%5B%22categories.level1"
                                  "%3AMarcas%20%2F%2F%2F%20LG%22%5D%5D&page="
                                  "{}".format(page)
                    }
                ]
            })
            url_webpage = 'https://wlt832ea3j-dsn.algolia.net/1/indexes/*/' \
                          'queries?x-algolia-application-id=WLT832EA3J&x-' \
                          'algolia-api-key=YTYwZjI3ODFjOTI3YWQ0MjJmYzQ3ZjB' \
                          'iNmY1Y2FiYjRhZjNiMmM3NmMxYTMyNDUwOGUxYjhkMWFhMz' \
                          'FlOGExNnRhZ0ZpbHRlcnM9'
            print(url_webpage)
            response = session.post(url_webpage, data=body)
            product_json = json.loads(response.text)['results'][0]['hits']

            if not product_json:
                if page == 1:
                    logging.warning('empty site')
                break
            for product in product_json:
                product_url = product['url']
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'page-title').text.strip()
        sku = soup.find('form', {'id': 'product_addtocart_form'})[
            'data-product-sku']
        stock = -1
        price = Decimal(
            soup.find('span', 'price').text.split('C$')[1].replace(',', ''))
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'product media').findAll('img')]
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
            'NIO',
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
