import json
import math

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Entel(Store):
    prepago_url = 'http://www.entel.cl/prepago/'

    @classmethod
    def categories(cls):
        return [
            'Cell',
            'CellPlan'
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_entries = defaultdict(lambda: [])

        if category == 'Cell':
            # Contrato

            json_url = 'https://miportal.entel.cl/lista-productos?' \
                       'No=0&Nrpp=1000&subPath=main%5B1%5D&format=json-rest'
            session.headers['Content-Type'] = 'application/json; charset=UTF-8'
            response = session.get(json_url)

            json_product_list = json.loads(
                response.text)['response']['records']

            for idx, device in enumerate(json_product_list):
                product_url = 'https://miportal.entel.cl/personas/producto{}'\
                    .format(device['detailsAction']['recordState'])

                product_entries[product_url].append({
                    'category_weight': 1,
                    'section_name': 'Equipos',
                    'value': idx + 1
                })

        if category == 'CellPlan':
            product_entries[cls.prepago_url].append({
                'category_weight': 1,
                'section_name': 'Planes',
                'value': 1
            })
            product_entries['http://www.entel.cl/planes/'].append({
                'category_weight': 1,
                'section_name': 'Planes',
                'value': 2
            })

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        products = []
        if url == cls.prepago_url:
            # Plan Prepago
            products.append(Product(
                'Entel Prepago',
                cls.__name__,
                category,
                url,
                url,
                'Entel Prepago',
                -1,
                Decimal(0),
                Decimal(0),
                'CLP',
            ))

        elif 'entel.cl/planes/' in url:
            # Plan Postpago
            products.extend(cls._plans(url, extra_args))
        elif 'miportal.entel.cl' in url:
            # Equipo postpago
            products.extend(cls._celular_postpago(url, extra_args))
        else:
            raise Exception('Invalid URL: ' + url)
        return products

    @classmethod
    def _plans(cls, url, extra_args):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        products = []

        for plan_box in soup.findAll('div', 'plan-box'):
            base_plan_name = plan_box.find('h3').text.strip()

            for suffix in ['', ' Portabilidad']:
                name = '{}{}'.format(base_plan_name, suffix)

                price_text = plan_box.find(
                    'p', 'txt-price').text.replace('/mes', '')

                price = Decimal(remove_words(price_text))

                products.append(Product(
                    name,
                    cls.__name__,
                    'CellPlan',
                    url,
                    url,
                    name,
                    -1,
                    price,
                    price,
                    'CLP'
                ))
        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        session = session_with_proxy(extra_args)

        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        raw_json = soup.find(
            'div', {'id': 'productDetail'}).find('script').string

        json_data = json.loads(raw_json)

        products = []

        for variant in json_data['renderSkusBean']['skus']:
            variant_name = variant['skuName']
            variant_sku = variant['skuId']

            plans_url = 'https://miportal.entel.cl/' \
                        'restpp/equipments/prices/{}'.format(variant_sku)

            plans_data = json.loads(
                session.get(plans_url).text)['response']['Prices']

            print(json.dumps(plans_data, indent=2))

            suffix_dict = {
                'Portabilidad': ' Portabilidad',
                'Venta': ''
            }

            for plan in plans_data:
                if plan['orderArea'] == 'Activacion de Linea':
                    continue

                if plan['planDisplayName'] == 'Conectado SIMple 7.990':
                    continue

                plan_name = plan['planDisplayName'] + \
                    suffix_dict[plan['orderArea']]

                if plan['planCommercePrice']:
                    field = 'planCommercePrice'
                else:
                    field = 'planListPrice'

                plan_price = Decimal(round(plan[field]))

                products.append(Product(
                    variant_name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    '{} - {}'.format(variant_sku, plan_name),
                    -1,
                    plan_price,
                    plan_price,
                    'CLP',
                    sku=variant_sku,
                    cell_monthly_payment=Decimal(0),
                    cell_plan_name=plan_name,
                ))

        return products
