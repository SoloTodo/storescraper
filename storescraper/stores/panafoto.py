import json
import logging
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Panafoto(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        endpoint = 'https://wlt832ea3j-dsn.algolia.net/1/indexes/*/queries?' \
                   'x-algolia-agent=Algolia%20for%20vanilla%20' \
                   'JavaScript%20(lite)%203.27.0%3Binstantsearch.js%20' \
                   '2.10.2%3BMagento2%20integration%20(1.10.0)%3BJS%20' \
                   'Helper%202.26.0&x-algolia-application-id=WLT832EA3J&x-alg'\
                   'olia-api-key=NzQyZDYyYTYwZGRiZDBjNjg0YjJmZDEyNWMyMTAyNTNh'\
                   'MjBjMDJiNzBhY2YyZWVjYWNjNzVjNjU5M2M5ZmVhY3RhZ0ZpbHRlcnM9'

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        session.headers['Referer'] = 'https://www.panafoto.com/'

        product_urls = []

        if category != TELEVISION:
            return []

        page = 0

        while True:
            payload_params = "page={}&facetFilters={}&numericFilters=%5B" \
                             "%22visibility_catalog%3D1%22%5D" \
                             "".format(page, urllib.parse.quote(
                                '[["manufacturer:LG"]]'))

            payload = {"requests": [
                {"indexName": "wwwpanafotocom_default_products",
                 "params": payload_params}]}

            response = session.post(endpoint, data=json.dumps(payload))
            products_json = json.loads(response.text)['results'][0]['hits']

            if not products_json:
                if page == 0:
                    logging.warning('Empty category:')
                break

            for product_json in products_json:
                product_url = product_json['url']
                if isinstance(product_url, list):
                    product_url = ','.join(product_url)

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

        data = response.text
        soup = BeautifulSoup(data, 'html.parser')
        product_json = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)

        name = product_json['name']
        sku = product_json['sku']
        model_label = soup.find('div', 'attibute-label', text='Modelo')
        part_number = model_label.next.next.text.strip()
        name = '{} - {}'.format(part_number, name)
        price = Decimal(product_json['offers']['price'])

        if product_json['offers']['availability'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        description = html_to_markdown(
            str(soup.find('div', {'id': 'description'})))

        pictures_tag = None

        for tag in soup.findAll('script', {'type': 'text/x-magento-init'}):
            if 'data-gallery-role=gallery-placeholder' in tag.text:
                pictures_tag = tag
                break

        pictures = json.loads(pictures_tag.text)[
            '[data-gallery-role=gallery-placeholder]'][
            'mage/gallery/gallery']['data']

        picture_urls = [e['full'] for e in pictures]

        variants_tag = soup.find('select', 'product-custom-option')

        if variants_tag:
            suffixes = [' ' + tag.text.strip() for tag in
                        variants_tag.findAll('option')[1:]]
        else:
            suffixes = ['']

        products = []

        for suffix in suffixes:
            products.append(Product(
                name + suffix,
                cls.__name__,
                category,
                url,
                url,
                sku + suffix,
                stock,
                price,
                price,
                'USD',
                sku=sku,
                part_number=part_number,
                description=description,
                picture_urls=picture_urls
            ))

        return products
