import json
import logging

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13, session_with_proxy
from storescraper.categories import AIR_CONDITIONER, OVEN, WASHING_MACHINE, \
    REFRIGERATOR, STEREO_SYSTEM, TELEVISION


class Marcimex(Store):
    @classmethod
    def categories(cls):
        return [WASHING_MACHINE]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != WASHING_MACHINE:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1
        while True:
            if page >= 10:
                raise Exception('Page overflow')

            url = 'https://www.marcimex.com/lg?page={}'.format(page)
            print(url)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')

            page_state = json.loads(
                soup.find('template', {'data-varname': '__STATE__'}).find(
                    'script').string)
            product_ids = []

            for key, value in page_state.items():
                if value.get('__typename', None) != 'ProductSearch':
                    continue
                product_ids = [x['id'] for x in value['products']]
                break

            if not product_ids:
                if page == 1:
                    raise Exception('Empty page')
                break

            for product_id in product_ids:
                product_entry = page_state[product_id]
                product_url = 'https://www.marcimex.com/{}/p'.format(
                    product_entry['linkText'])
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        product_data = json.loads(
            soup.find('template', {'data-varname': '__STATE__'}).find(
                'script').string)

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        item_key = '{}.items.0'.format(base_json_key)
        key = product_data[item_key]['itemId']
        ean = product_data[item_key]['ean']
        if not check_ean13(ean):
            ean = None

        name = product_specs['productName']
        sku = product_specs['productReference']
        description = product_specs.get('description', None)

        pricing_key = '${}.items.0.sellers.0.commertialOffer'.format(
            base_json_key)
        pricing_data = product_data[pricing_key]

        price = Decimal(str(pricing_data['Price'])) + \
            Decimal(str(pricing_data['Tax']))
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
            key,
            stock,
            price,
            price,
            'USD',
            sku=sku,
            ean=ean,
            description=description,
            picture_urls=picture_urls,
            part_number=sku
        )

        return [p]
