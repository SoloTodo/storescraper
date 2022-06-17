import json
import logging
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
    currency = 'USD'

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = cls._category_paths()
        discovered_urls = []
        session = session_with_proxy(extra_args)
        session.headers['content-type'] = 'application/x-www-form-urlencoded'
        skip_unavailable = extra_args and extra_args.get('skip_unavailable')

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

            if skip_unavailable:
                payload += '&obsOnly=Y'

            json_response = json.loads(
                session.post(endpoint_url, payload).text)
            product_entries = json_response['data'][0]['productList']

            if not product_entries:
                logging.warning('Empty category: {} - {}'.format(
                    category_id, is_active))

            for product_entry in product_entries:
                product_url = cls.base_url + product_entry['modelUrlPath']
                discovered_urls.append(product_url)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=20)
        skip_unavailable = extra_args and extra_args.get('skip_unavailable')

        if response.url != url or response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        model_id = soup.find('input', {'id': 'modelId'})['value']
        model_data = cls._retrieve_api_model(model_id)
        sibling_groups = model_data['siblings']
        sibling_ids = [model_id]

        for sibling_group in sibling_groups:
            if sibling_group['siblingType'] in ['COLOR', 'SIZE', 'CAPACITY']:
                for sibling in sibling_group['siblingModels']:
                    if sibling['modelId'] not in sibling_ids:
                        sibling_ids.append(sibling['modelId'])
            else:
                raise Exception('Unknown sibling type for: ' + url)

        products = []

        for sibling_id in sibling_ids:
            sibling = cls._retrieve_single_product(sibling_id, category)
            if sibling:
                if skip_unavailable and sibling.stock == 0:
                    continue
                products.append(sibling)

        return products

    @classmethod
    def _retrieve_single_product(cls, model_id, category):
        print(model_id)
        model_data = cls._retrieve_api_model(model_id)

        if model_data['modelStatusCode'] == 'SUSPENDED':
            return None

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

        # Unavailable products do not have a price, but we still need to
        # return them by default because the Where To Buy (WTB) system
        # needs to consider all products, so use zero as default.
        if model_data['obsInventoryFlag'] == 'Y':
            price = Decimal(model_data['obsSellingPrice'])
            stock = -1
        else:
            price = Decimal(0)
            stock = 0

        picture_urls = [cls.base_url + x['largeImageAddr'].replace(' ', '%20')
                        for x in model_data['galleryImages']]
        picture_urls = [x for x in picture_urls if validators.url(x)]
        if not picture_urls:
            picture_urls = None

        url = cls.base_url + model_data['modelUrlPath']

        content = requests.get(url).text

        section_data = re.search(r'_dl =([{\S\s]+\});', content)

        if not section_data:
            return None

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

        assert len(section_data['products']) == 1

        sku = section_data['products'][0]['sales_model_code']

        # If LG does not provide a full model name (model name with suffix,
        # such as "GF22BGSK1.ASTPECL") use the base model name ("GF22BGSK1")
        # and add a dot as some queries rely on having a dot as the separator.
        if not sku:
            sku = model_name + '.'

        description = '. '.join([x['bulletFeatureDesc']
                                 for x in model_data['bulletFeatures']])

        return Product(
            name[:250],
            cls.__name__,
            category,
            url,
            url,
            model_id,
            stock,
            price,
            price,
            cls.currency,
            sku=sku,
            picture_urls=picture_urls,
            part_number=sku,
            positions=positions,
            description=description
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
