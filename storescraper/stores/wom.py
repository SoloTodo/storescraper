import json
import time

from collections import defaultdict
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, HeadlessChrome


class Wom(Store):
    prepago_url = 'http://www.wom.cl/prepago/'
    planes_url = 'https://store.wom.cl/planes/'

    @classmethod
    def categories(cls):
        return [
            'CellPlan',
            'Cell'
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        discovered_entries = defaultdict(lambda: [])

        if category == 'CellPlan':
            discovered_entries[cls.prepago_url].append({
                'category_weight': 1,
                'section_name': 'Planes',
                'value': 1
            })

            discovered_entries[cls.planes_url].append({
                'category_weight': 1,
                'section_name': 'Planes',
                'value': 2
            })

        elif category == 'Cell':
            session = session_with_proxy(extra_args)
            equipos_url = 'https://store-srv.wom.cl/rest/V1/content/getList?' \
                          'searchCriteria[filterGroups][0][filters][0]' \
                          '[field]=attribute_set_id&searchCriteria' \
                          '[filterGroups][0][filters][0][value]=11&' \
                          'searchCriteria[filterGroups][1][filters][0]' \
                          '[field]=type_id&searchCriteria[filterGroups][1]' \
                          '[filters][0][value]=configurable&searchCriteria' \
                          '[pageSize]=200&searchCriteria[currentPage]=1&' \
                          'searchCriteria[filterGroups][2][filters][0]' \
                          '[field]=name&searchCriteria[filterGroups][2]' \
                          '[filters][0][value]=%25%25&searchCriteria' \
                          '[filterGroups][2][filters][0]' \
                          '[condition_type]=like&searchCriteria[sortOrders]' \
                          '[0][field]=&searchCriteria[filterGroups][10]' \
                          '[filters][0][field]=status&searchCriteria' \
                          '[filterGroups][10][filters][0][value]=1'
            response = session.get(equipos_url)

            json_response = json.loads(response.text)

            for idx, cell_entry in enumerate(json_response['items']):
                cell_url = 'https://store.wom.cl/equipos/' + \
                           str(cell_entry['sku']) + '/' + cell_entry[
                               'name'].replace('+', 'plus').replace(
                                '.', '-').replace(' ', '-')
                discovered_entries[cell_url].append({
                    'category_weight': 1,
                    'section_name': 'Equipos',
                    'value': idx + 1
                })

        return discovered_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = []
        if url == cls.prepago_url:
            # Plan Prepago
            p = Product(
                'WOM Prepago',
                cls.__name__,
                category,
                url,
                url,
                'WOM Prepago',
                -1,
                Decimal(0),
                Decimal(0),
                'CLP',
            )
            products.append(p)
        elif url == cls.planes_url:
            # Plan Postpago
            products.extend(cls._plans(url, extra_args))
        elif '/equipos/' in url:
            # Equipo postpago
            products.extend(cls._celular_postpago(url, extra_args))
        else:
            raise Exception('Invalid URL: ' + url)
        return products

    @classmethod
    def _plans(cls, url, extra_args):
        with HeadlessChrome() as driver:
            driver.get('https://store.wom.cl/planes/')
            retries = 5
            plan_containers = None

            while retries:
                plan_containers = driver.find_elements_by_class_name(
                    'index-module--planItemWrapper--1HvWb')
                if plan_containers:
                    break
                time.sleep(2)
                retries -= 1

            if not plan_containers:
                raise Exception('No plan tags found')

            soup = BeautifulSoup(driver.page_source, 'html.parser')

        plan_containers = soup.findAll(
            'div', 'index-module--planItemWrapper--1HvWb')
        products = []

        variants = [
            'sin cuota de arriendo',
            'con cuota de arriendo',
        ]

        for container in plan_containers:
            plan_name = container.find(
                'div', 'index-module--value--3xbFh').text
            plan_price = Decimal(remove_words(
                container.find('span', 'index-module--price--1k_ac').text))

            for variant in variants:
                for suffix in ['', ' Portabilidad']:
                    adjusted_plan_name = '{}{} ({})'.format(
                        plan_name, suffix, variant)

                    products.append(Product(
                        adjusted_plan_name,
                        cls.__name__,
                        'CellPlan',
                        url,
                        url,
                        adjusted_plan_name,
                        -1,
                        plan_price,
                        plan_price,
                        'CLP',
                    ))

        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        print(url)
        session = session_with_proxy(extra_args)

        path = url.split('/', 3)[-1]
        endpoint = 'https://store.wom.cl/page-data/{}/' \
                   'page-data.json'.format(path)
        response = session.get(endpoint)

        if response.status_code == 404:
            return []

        json_data = response.json()
        products = []
        plans = [
            'WOM Plan 40 GB',
            'WOM Plan 100 GB',
            'WOM Plan 200 GB',
            'WOM Plan 300 GB',
            'WOM Plan 400 GB',
            'WOM Plan 500 GB',
            'WOM Plan Libre',
        ]

        for entry in json_data['result']['data']['contentfulProduct'][
                'productVariations']:
            name = entry['name']
            context = json.loads(entry['context']['context'])
            graphql_data = json.loads(context['graphql_data'])

            stock_reference = entry['referenceId']
            stock_endoint = 'https://store.wom.cl/ss/{}.json'.format(
                stock_reference.replace('.', '_'))
            stock_json = json.loads(session.get(stock_endoint).text)

            if stock_json['inventory']:
                stock = -1
            else:
                stock = 0

            portability_choices = [
                ('', 'newConnection'),
                (' Portabilidad', 'portIn'),
            ]

            for portability_name_suffix, portability_json_field in \
                    portability_choices:
                price_without_installments = None
                initial_price_with_installments = None
                installment_price = None

                for related_price in graphql_data['productOfferingPrice'][
                        portability_json_field]['relatedPrice']:
                    if related_price['priceType'] == 'price':
                        price_without_installments = Decimal(
                            related_price['price']['value'])
                    elif related_price['priceType'] == 'initialPrice':
                        initial_price_with_installments = Decimal(
                            related_price['price']['value'])
                    elif related_price['priceType'] == 'installmentPrice':
                        installment_price = Decimal(
                            related_price['price']['value'])

                if price_without_installments is None \
                        or initial_price_with_installments is None \
                        or installment_price is None:
                    return []

                # assert price_without_installments is not None
                # assert initial_price_with_installments is not None
                # assert installment_price is not None

                for plan in plans:
                    # Without installments
                    products.append(Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} {}{}'.format(name, plan, portability_name_suffix),
                        stock,
                        price_without_installments,
                        price_without_installments,
                        'CLP',
                        cell_plan_name='{}{}'.format(
                            plan,
                            portability_name_suffix,
                        ),
                        cell_monthly_payment=Decimal(0)
                    ))

                    # With installments
                    products.append(Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} {}{} Cuotas'.format(name, plan,
                                                portability_name_suffix),
                        stock,
                        initial_price_with_installments,
                        initial_price_with_installments,
                        'CLP',
                        cell_plan_name='{}{} Cuotas'.format(
                            plan,
                            portability_name_suffix,
                        ),
                        cell_monthly_payment=installment_price
                    ))

            # Prepaid
            prepaid_price = Decimal(
                graphql_data['productOfferingPrice']['standard'][
                    'relatedPrice'][0]['price']['value'])

            products.append(Product(
                name,
                cls.__name__,
                'Cell',
                url,
                url,
                '{} Prepago'.format(name),
                stock,
                prepaid_price,
                prepaid_price,
                'CLP',
                cell_plan_name='WOM Prepago'
            ))

        return products
