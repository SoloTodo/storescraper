import json
from decimal import Decimal
import logging
import re
import time

from bs4 import BeautifulSoup

from storescraper.categories import WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Woow(Store):
    @classmethod
    def categories(cls):
        return [
            WASHING_MACHINE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extension = [
            WASHING_MACHINE
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extension:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception('page overflow: ' + local_category)
                url_webpage = 'https://shop.tata.com.uy/lg/lg?_q=lg&fuzzy=0' \
                    '&initialMap=ft&initialQuery=lg&map=brand,ft&operator=a' \
                    'nd&page={}'.format(page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')

                if 'oops!' in soup.text:
                    if page == 1:
                        logging.warning('Empty category: ' + local_category)
                    break

                template = soup.find('template', {'data-varname': '__STATE__'})
                item_list = json.loads(template.text)
                for k in item_list.keys():
                    if 'linkText' in item_list[k]:
                        product = item_list[k]['linkText']
                        product_urls.append(
                            f"https://shop.tata.com.uy/{product}/p")

                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        product_data = json.loads(soup.find(
            'template', {'data-varname': '__STATE__'}).text)

        base_json_keys = list(product_data.keys())

        if not base_json_keys:
            return []

        base_json_key = base_json_keys[0]

        item_key = '{}.items.0'.format(
            base_json_key)

        product_specs = product_data[item_key]

        name = product_specs['name']
        sku = str(product_specs['itemId'])

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
            'UYU',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
