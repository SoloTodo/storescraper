import json

import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class MovistarOne(Store):
    url = 'http://hogar.movistar.cl/movistarone/'

    @classmethod
    def categories(cls):
        return [
            'Cell',
            'CellPlan'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category == 'Cell':
            return [cls.url]

        return []

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        if url != cls.url:
            return []

        session = session_with_proxy(extra_args)
        products = []

        raw_js = session.get(
            'http://hogar.movistar.cl/movistarone/dev/js/'
            'MovistarOneV3.js').text

        cell_associations = json.loads(
            re.search(r'var data = ([^;]*)', raw_js).groups()[0])

        plans_dict = cell_associations['plans']

        cell_pricing_dict = cell_associations['products']

        page_soup = BeautifulSoup(session.get(url).text, 'html.parser')
        product_options = page_soup.find(
            'select', {'id': 'sim_product'}).findAll('option')[1:]
        plan_options = page_soup.find(
            'select', {'id': 'sim_plan'}).findAll('option')[1:]

        for product_option in product_options:
            product_id = product_option['value']
            product_entry = cell_pricing_dict[product_id]
            cell_name = product_entry['spec']['name'].strip()

            for plan_option in plan_options:
                plan_code = plan_option['value']
                plan_data = product_entry['plan'][plan_code]
                plan_name = plans_dict[plan_code]['name']
                price = Decimal(remove_words(
                    plan_data['initial_amount']))
                name = cell_name + ' / ' + plan_name

                cell_monthly_payment = Decimal(
                    remove_words(plan_data['fee'].split('$')[1]))

                product = Product(
                    cell_name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    name,
                    -1,
                    price,
                    price,
                    'CLP',
                    cell_plan_name=plan_name,
                    cell_monthly_payment=cell_monthly_payment
                )
                products.append(product)
        return products
