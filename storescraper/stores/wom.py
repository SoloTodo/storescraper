import json
from collections import defaultdict
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Wom(Store):
    prepago_url = 'https://www.wom.cl/prepago/'
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
                allow_zero_prices=True
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
        variants = [
            'sin cuota de arriendo',
            'con cuota de arriendo',
        ]
        products = []

        for plan_json in extra_args['plans_json']:
            plan_name = plan_json['name']
            product_data = json.loads(plan_json['context']['context'])
            plan_price = Decimal(product_data['price'])

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

        if 'SEMINUEVO' in json_data['result']['data']['contentfulProduct'][
                'name'].upper():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        products = []
        plans = ['WOM ' + plan_choice['name']
                 for plan_choice in extra_args['plans_json']]

        variations = json_data['result']['data']['contentfulProduct'][
                'productVariations']

        if not variations:
            return []

        for entry in variations:
            name = entry['name']
            context = json.loads(entry['context']['context'])
            if not context['graphql_data']:
                continue
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
                    elif related_price['priceType'] == 'installmentPrice' \
                            and related_price['recurringChargePeriodType']:
                        installment_price = Decimal(
                            related_price['price']['value'])

                if price_without_installments is None \
                        or initial_price_with_installments is None \
                        or installment_price is None:
                    return []

                assert price_without_installments is not None
                assert initial_price_with_installments is not None
                assert installment_price is not None

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
                        condition=condition,
                        cell_plan_name='{}{}'.format(
                            plan,
                            portability_name_suffix,
                        ),
                        cell_monthly_payment=Decimal(0),
                        allow_zero_prices=True
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
                        condition=condition,
                        cell_plan_name='{}{} Cuotas'.format(
                            plan,
                            portability_name_suffix,
                        ),
                        cell_monthly_payment=installment_price,
                        allow_zero_prices=True
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
                condition=condition,
                cell_plan_name='WOM Prepago'
            ))

        return products

    @classmethod
    def preflight(cls, extra_args=None):
        # Obtain valid plans
        session = session_with_proxy(extra_args)

        response = session.get('https://store.wom.cl/page-data/sq/d/'
                               '2591293040.json')

        data = response.json()
        plans_json = []

        for product_entry in data['data']['allContentfulProduct']['nodes']:
            if not product_entry['offer'] and not product_entry['offerPdp']:
                continue

            plans_json.append(product_entry)

        return {
            'plans_json': plans_json
        }
