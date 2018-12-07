import json

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
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        if category == 'Cell':
            # Contrato

            json_product_list = json.loads(session.get(
                'http://equipos.entel.cl/devices/personas/tm/'
                'contratacion.json?search=1').text)

            for device in json_product_list['devices']:
                product_url = 'http://equipos.entel.cl/segmentos/' \
                              'personas/products/' + device['slug']
                product_urls.append(product_url)

        if category == 'CellPlan':
            product_urls.append(cls.prepago_url)
            product_urls.append('http://www.entel.cl/planes/')

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
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
        elif 'equipos.entel.cl' in url:
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

        variants = [
            'sin cuota de arriendo',
            'con cuota de arriendo',
        ]

        for plan_box in soup.findAll('div', 'box-planes'):
            base_plan_name = plan_box.find('h3').text.split('$')[0].strip()

            for suffix in ['', ' Portabilidad']:
                for variant in variants:
                    name = '{}{} ({})'.format(base_plan_name, suffix, variant)

                    price_container = plan_box.find(
                        'span', 'green-txt')

                    price = Decimal(remove_words(price_container.text))

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
                        'CLP',
                    ))
        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        session = session_with_proxy(extra_args)
        slug = url.split('/')[-1]

        details_url = 'https://equipos.entel.cl/device/{}.json'.format(slug)
        details_json = json.loads(session.get(details_url).text)
        product_name = details_json['title']
        products = []
        pricing_variants = {}

        for variant in details_json['variants']:
            pricing_variant = None
            variant_name = product_name

            variant_items = sorted(variant['options'].items(),
                                   key=lambda x: x[0])

            for key, value in variant_items:
                variant_name += ' {} {}'.format(key, value)
                if key == 'capacidad':
                    print('Found: ' + value)
                    if value not in pricing_variants:
                        print('New value')
                        pricing_variants[value] = variant
                    pricing_variant = pricing_variants[value]

            if not pricing_variant:
                print('Using default')
                pricing_variant = variant

            picture_urls = variant['covers']

            # Plan

            plan_choices = [
                ('',
                 ('price_1',),
                 'sale_price_promotion',
                 'sale_price'
                 ),
                (' Portabilidad',
                 ('portability_price_promotion', 'price_1'),
                 'portability_price',
                 'discount_percentage'
                 ),
            ]

            # Use the prices of the first variant with the same capacity
            for plan in pricing_variant['plans']:
                plan = plan['plan']

                if plan['plan_type'] in ['cargo_fijo', 'voz',
                                         'multi_smart',
                                         'cuenta_controlada']:
                    continue

                if plan['modality'] != 'contratacion':
                    continue

                for plan_suffix, field_names, monthly_payment_field, \
                        direct_buy_field in plan_choices:
                    base_plan_name = plan['title'] + plan_suffix
                    base_plan_name = base_plan_name.replace('*', '').strip()

                    for field_name in field_names:
                        price = plan[field_name]

                        if price is None:
                            continue

                        price = Decimal(price)

                        if price < 0:
                            continue

                        if 0 < price < 100:
                            price = Decimal(plan['price_1'])
                            if price < 0:
                                continue

                        break

                    cell_monthly_payment = Decimal(plan[monthly_payment_field])
                    buyout_payment = Decimal(plan[direct_buy_field])

                    plan_name = base_plan_name

                    # Con cuota de arriendo

                    products.append(Product(
                        variant_name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} - {} Cuotas'.format(variant_name, plan_name),
                        -1,
                        price,
                        price,
                        'CLP',
                        cell_plan_name=plan_name + ' Cuotas',
                        picture_urls=picture_urls,
                        cell_monthly_payment=cell_monthly_payment
                    ))

                    # Sin cuota de arriendo

                    products.append(Product(
                        variant_name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} - {}'.format(variant_name, plan_name),
                        -1,
                        buyout_payment,
                        buyout_payment,
                        'CLP',
                        cell_plan_name=plan_name,
                        picture_urls=picture_urls,
                        cell_monthly_payment=Decimal(0)
                    ))

            prepaid_prices = pricing_variant['prepaid_prices']

            if prepaid_prices:
                prepago_price = Decimal(
                    pricing_variant['prepaid_prices']['sale_price'])

                product = Product(
                    variant_name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    '{} - Entel Prepago'.format(variant_name),
                    -1,
                    prepago_price,
                    prepago_price,
                    'CLP',
                    cell_plan_name='Entel Prepago',
                    picture_urls=picture_urls
                )
                products.append(product)

        return products
