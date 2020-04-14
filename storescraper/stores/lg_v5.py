import json
import re

import demjson
import requests
import validators
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class LgV5(Store):
    base_url = 'https://www.lg.com'
    region_code = property(lambda self: 'Subclasses must implement this')

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = cls._category_paths()
        discovered_urls = []
        session = session_with_proxy(extra_args)
        session.headers['content-type'] = 'application/x-www-form-urlencoded'

        endpoint_url = 'https://www.lg.com/{}/mkt/ajax/category/' \
                       'retrieveCategoryProductList'.format(cls.region_code)

        for category_id, local_category, is_active in \
                category_paths:
            if local_category != category:
                continue

            if is_active:
                status = 'ACTIVE'
            else:
                status = 'DISCONTINUED'

            payload = 'categoryId={}&modelStatusCode={}&bizType=B2C&viewAll' \
                      '=Y'.format(category_id, status)
            json_response = json.loads(
                session.post(endpoint_url, payload).text)
            product_entries = json_response['data'][0]['productList']

            if not product_entries:
                raise Exception('Empty category: {} - {}'.format(
                    category_id, is_active))

            for product_entry in product_entries:
                product_url = cls.base_url + product_entry['modelUrlPath']
                discovered_urls.append(product_url)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=20)

        if response.url != url:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        model_id = soup.find('input', {'name': 'modelId'})['value']
        model_data = cls._retrieve_api_model(model_id)
        sibling_groups = model_data['siblings']
        sibling_ids = [model_id]

        for sibling_group in sibling_groups:
            if sibling_group['siblingType'] == 'SIZE':
                # Already considered when detecting entries
                continue
            elif sibling_group['siblingType'] == 'COLOR':
                for sibling in sibling_group['siblingModels']:
                    if sibling['modelId'] not in sibling_ids:
                        sibling_ids.append(sibling['modelId'])
            else:
                raise Exception('Unkown sibling type for: ' + url)

        products = []

        for sibling_id in sibling_ids:
            products.append(cls._retrieve_single_product(sibling_id, category))

        return products

    @classmethod
    def _retrieve_single_product(cls, model_id, category):
        print(model_id)
        model_data = cls._retrieve_api_model(model_id)
        model_name = model_data['modelName']
        color = None
        short_description = model_data['userFriendlyName']

        for sibling_entry in model_data['siblings']:
            if sibling_entry['siblingType'] == 'COLOR':
                for sibling in sibling_entry['siblingModels']:
                    if sibling['modelId'] == model_id:
                        color = sibling['siblingValue'].strip()

        if color:
            name = '{} ({} / {})'.format(short_description, model_name, color)
        else:
            name = '{} - {}'.format(model_name, short_description)

        picture_urls = [cls.base_url + x['largeImageAddr']
                        for x in model_data['galleryImages']]
        picture_urls = [x for x in picture_urls if validators.url(x)]
        if not picture_urls:
            picture_urls = None

        url = cls.base_url + model_data['modelUrlPath']

        content = requests.get(url).text
        section_data = re.search(r'_dl =([{\S\s]+\});', content)
        section_data = demjson.decode(section_data.groups()[0])

        field_candidates = [
            'page_category_l4', 'page_category_l3', 'page_category_l2',
            'page_category_l1'
        ]

        for candidate in field_candidates:
            if not section_data[candidate]:
                continue

            section_paths = section_data[candidate].split(':')[1:]
            section_path = ' > '.join([x for x in section_paths if x.strip()])
            positions = {
                section_path: 1
            }
            break
        else:
            raise Exception('At least one of the section candidates should '
                            'have matched')

        return Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            model_id,
            -1,
            Decimal(0),
            Decimal(0),
            'USD',
            sku=model_name,
            picture_urls=picture_urls,
            positions=positions
        )

    @classmethod
    def _ajax_endpoint(cls):
        return '{}/{}/mkt/ajax/product/retrieveSiblingProductInfo'.format(
                cls.base_url, cls.region_code
            )

    @classmethod
    def _retrieve_api_model(cls, model_id):
        session = requests.Session()
        session.headers['content-type'] = 'application/x-www-form-urlencoded'
        payload = 'modelId={}'.format(model_id)
        product_data = json.loads(
            session.post(cls._ajax_endpoint(), payload).text)
        return product_data['data'][0]

    @classmethod
    def _category_paths(cls):
        raise NotImplementedError('Subclasses must implement this method')
