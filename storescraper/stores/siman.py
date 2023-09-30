import base64
import json
from decimal import Decimal
import re

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, vtex_preflight


class Siman(Store):
    country_url = ''
    currency_iso = ''

    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []
        product_urls = []
        session = session_with_proxy(extra_args)

        offset = 0
        while True:
            if offset >= 190:
                raise Exception('Page overflow')

            variables = {
                "from": offset,
                "to": offset + 19,
                "selectedFacets": [{"key": "b", "value": 'lg'}]
            }

            payload = {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": extra_args['sha256Hash']
                },
                "variables": base64.b64encode(json.dumps(
                    variables).encode('utf-8')).decode('utf-8')
            }

            endpoint = 'https://{}.siman.com/_v/segment/graphql/v1' \
                       '?extensions={}'.format(
                        cls.country_url, json.dumps(payload))
            response = session.get(endpoint).json()

            product_entries = response['data']['productSearch']['products']

            if not product_entries:
                break

            for product_entry in product_entries:
                product_url = 'https://{}.siman.com/{}/p'.format(
                    cls.country_url, product_entry['linkText'])
                product_urls.append(product_url)

            offset += 19

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')

        product_state_tag = soup.find('template',
                                      {'data-varname': '__STATE__'})
        if product_state_tag:
            product_state_tag = product_state_tag.find('script').string
        else:
            product_state_tag = '{' + re.search(
                r'__STATE__ = {(.+)}', soup.text).groups()[0] + '}'
        product_data = json.loads(product_state_tag)

        if not product_data:
            return []

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        if product_specs['brand'] != 'LG':
            return []

        name = product_specs['productName']
        sku = product_specs['productReference']
        description = product_specs.get('description', None)

        pricing_key = '${}.items.0.sellers.0.commertialOffer'.format(
            base_json_key)
        pricing_data = product_data[pricing_key]

        price = Decimal(str(pricing_data['Price']))
        stock = pricing_data['AvailableQuantity']

        picture_list_key = '{}.items.0'.format(base_json_key)
        picture_list_node = product_data[picture_list_key]
        picture_ids = [x['id'] for x in picture_list_node['images']]

        picture_urls = []
        for picture_id in picture_ids:
            picture_node = product_data[picture_id]
            picture_urls.append(picture_node['imageUrl'].split('?')[0])

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
            cls.currency_iso,
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]

    @classmethod
    def preflight(cls, extra_args=None):
        return vtex_preflight(
            extra_args, 'https://{}.siman.com/tecnologia/pantallas'.format(
                cls.country_url))
