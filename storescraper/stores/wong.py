from decimal import Decimal
import json
import logging

from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13, html_to_markdown, \
    session_with_proxy


class Wong(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1
        while True:
            if page > 20:
                raise Exception('Page overflow')

            url_webpage = 'https://www.wong.pe/lg?page={}'.format(page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')

            json_data = json.loads(soup.findAll(
                'script', {'type': 'application/ld+json'})[-1].text)

            product_containers = json_data['itemListElement']
            if len(product_containers) == 0:
                if page == 1:
                    logging.warning('Empty category')
                break
            for container in product_containers:
                product_urls.append(container['item']['@id'])
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

        key = product_specs['productId']
        name = product_specs['productName']
        sku = product_specs['productReference']
        description = product_specs.get('description', None)
        if description:
            description = html_to_markdown(description)

        key_key = '{}.items.0'.format(base_json_key)
        ean = product_data[key_key].get('ean', None)

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
            key,
            stock,
            price,
            price,
            'PEN',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            ean=ean,
        )
        return [p]
