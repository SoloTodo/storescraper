import json
import logging
import urllib
from decimal import Decimal

from storescraper.categories import TELEVISION

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class AlKosto(Store):
    endpoint = 'https://qx5ips1b1q-dsn.algolia.net/1/indexes/*/queries?x-al' \
        'golia-agent=Algolia%20for%20JavaScript%20(4.5.1)%3B%20Brows' \
        'er%20(lite)%3B%20instantsearch.js%20(4.40.3)%3B%20JS%20Help' \
        'er%20(3.8.0)&x-algolia-api-key=04636813b7beb6abd08a7e35f8c8' \
        '80a1&x-algolia-application-id=QX5IPS1B1Q'

    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        product_urls = []

        if category != TELEVISION:
            return []

        page = 0

        while True:
            payload_params = "query=""&page={}&facetFilters={}" \
                             "".format(page, urllib.parse.quote(
                                 '[["brand_string_mv:LG"]]'))

            payload = {"requests": [
                {"indexName": "alkostoIndexAlgoliaPRD",
                 "params": payload_params}]}

            response = session.post(cls.endpoint, data=json.dumps(payload))
            products_json = json.loads(response.text)['results'][0]['hits']

            if not products_json:
                if page == 0:
                    logging.warning('Empty category:')
                break

            for product_json in products_json:
                product_url = product_json['url_es_string']

                product_urls.append('https://www.alkosto.com/' + product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)

        # Try and find the SKU in the URL
        query = url.split('/')[-1]
        payload_params = "query={}".format(query)

        payload = {"requests": [
            {"indexName": "alkostoIndexAlgoliaPRD",
             "params": payload_params}]}

        session = session_with_proxy(extra_args)
        response = session.post(cls.endpoint, data=json.dumps(payload))
        products_json = json.loads(response.text)['results'][0]['hits']

        for product_entry in products_json:
            if product_entry['url_es_string'] in url:
                raise Exception('Product without sku in url ' + url)

        name = product_entry['name_text_es']
        key = product_entry['code_string']
        stock = -1 if product_entry['instockflag_boolean'] else 0
        price = Decimal(str(product_entry['lowestprice_double']))
        picture_urls = ['https://www.alkosto.com/' +
                        product_entry['img-820wx820h_string']]

        return [Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'COP',
            sku=key,
            picture_urls=picture_urls
        )]
