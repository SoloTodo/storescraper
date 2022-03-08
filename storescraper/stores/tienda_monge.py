import json
import logging
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import CELL, TELEVISION, OPTICAL_DISK_PLAYER, \
    AIR_CONDITIONER, STOVE, OVEN, WASHING_MACHINE, REFRIGERATOR, \
    STEREO_SYSTEM, MONITOR, HEADPHONES


class TiendaMonge(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # KEEPS ONLY LG PRODUCTS

        if category != TELEVISION:
            return []

        endpoint = 'https://wlt832ea3j-dsn.algolia.net/1/indexes/*/queries?' \
                   'x-algolia-application-id=WLT832EA3J&x-algolia-api-key=' \
                   'YTYwZjI3ODFjOTI3YWQ0MjJmYzQ3ZjBiNmY1Y2FiYjRhZjNiMmM3Nm' \
                   'MxYTMyNDUwOGUxYjhkMWFhMzFlOGExNnRhZ0ZpbHRlcnM9'

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/json'
        product_urls = []

        payload_params = 'hitsPerPage=1000&facetFilters=["marca:LG"]'
        payload = {
            "requests": [
                {"indexName": "monge_upgrade_prod_default_products",
                 "params": payload_params}
            ]
        }

        response = session.post(endpoint, data=json.dumps(payload))
        products_json = json.loads(response.text)['results'][0]['hits']

        for product in products_json:
            product_urls.append(product['url'])

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name_container = soup.find(
            'span', {'data-ui-id': 'page-title-wrapper'})

        if not name_container:
            return []

        name = name_container.text.strip()
        sku = soup.find('div', 'value').text.strip()

        if soup.find('button', {'id': 'product-addtocart-button'}):
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('span', 'price').text
                        .replace('₡', '').replace('.', '').strip())

        picture_urls = [soup.find('img', {'alt': 'main product photo'})['src']]

        description = html_to_markdown(
            str(soup.find('div', 'product attribute description'))
        )

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
            'CRC',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
