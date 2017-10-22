import json
import urllib

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
            json_product_list = json.loads(session.get(
                'http://equipos.entel.cl/devices/personas/tm/'
                'contratacion.json?search=1').text)

            for device in json_product_list['devices']:
                product_url = 'http://equipos.entel.cl/segmentos/' \
                              'personas/products/' + device['slug']
                product_urls.append(product_url)

        if category == 'CellPlan':
            product_urls.append(cls.prepago_url)
            for path in ['index.iws', 'index2.iws']:
                plan_url = 'http://www.entel.cl/planes/' + path
                product_urls.append(plan_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = []
        if url == cls.prepago_url:
            # Plan Prepago
            p = Product(
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
            )
            products.append(p)
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

        plan_tabs = soup.find('div', {'class': 'row tabs'}).findAll(
            'div', 'tab')
        content_tabs = soup.find('div', 'content-tabs').findAll(
            'div', 'content-tab')

        products = []

        for plan_tab, content_tab in zip(plan_tabs, content_tabs):
            base_plan_name = plan_tab.text.replace('\n', ' ').strip()

            for suffix in ['', ' Portabilidad']:
                name = base_plan_name + suffix

                normal_price_container = content_tab.find(
                    'div', 'col3').find('p', 't2')
                highlighted_price = Decimal(remove_words(
                    content_tab.find('div', 'col3').find(
                        'p', 't4').text))

                if normal_price_container:
                    normal_price = Decimal(remove_words(
                        normal_price_container.text))
                    web_price = highlighted_price
                else:
                    normal_price = web_price = highlighted_price

                product = Product(
                    name,
                    cls.__name__,
                    'CellPlan',
                    url,
                    url,
                    name,
                    -1,
                    normal_price,
                    normal_price,
                    'CLP',
                )
                products.append(product)

                # Exclusivo web

                name = base_plan_name + suffix + ' Exclusivo Web'

                price = web_price.quantize(0)

                product = Product(
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
                )
                products.append(product)

        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        print(url)
        session = session_with_proxy(extra_args)
        slug = url.split('/')[-1]

        details_url = 'https://equipos.entel.cl/device/{}.json'.format(
            slug)

        details_json = json.loads(session.get(details_url).text)

        product_name = details_json['title']
        main_variant = details_json['variants'][0]

        products = []

        # Prepago

        try:
            prepago_price = Decimal(
                main_variant['prepaid_prices']['price_1'])
            prepago_stock = -1
        except TypeError:
            prepago_price = Decimal(0)
            prepago_stock = 0

        for variant in details_json['variants']:
            variant_name = product_name
            for key, value in variant['options'].items():
                variant_name += ' {} {}'.format(key, value)

            picture_urls = variant['covers']

            product = Product(
                variant_name,
                cls.__name__,
                'Cell',
                url,
                url,
                variant_name + ' Entel Prepago',
                prepago_stock,
                prepago_price,
                prepago_price,
                'CLP',
                cell_plan_name='Entel Prepago',
                picture_urls=picture_urls
            )
            products.append(product)

            # Plan

            plan_choices = [
                ('',
                 ('price_1',),
                 'sale_price_promotion'),
                (' Portabilidad',
                 ('portability_price_promotion', 'price_1'),
                 'portability_price'),
            ]

            # Yes, use the prices for the first variant for all variants
            for plan in main_variant['plans']:
                plan = plan['plan']
                if plan['plan_type'] in ['cargo_fijo', 'voz',
                                         'multi_smart',
                                         'cuenta_controlada']:
                    continue

                for plan_suffix, field_names, monthly_payment_field \
                        in plan_choices:
                    plan_name = plan['title'] + plan_suffix
                    plan_name = plan_name.replace('*', '').strip()

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

                    product = Product(
                        variant_name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} - {}'.format(variant_name, plan_name),
                        -1,
                        price,
                        price,
                        'CLP',
                        cell_plan_name=plan_name,
                        picture_urls=picture_urls,
                        cell_monthly_payment=cell_monthly_payment
                    )
                    products.append(product)

                    plan_name += ' Exclusivo Web'

                    product = Product(
                        variant_name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} - {}'.format(variant_name, plan_name),
                        -1,
                        price,
                        price,
                        'CLP',
                        cell_plan_name=plan_name,
                        picture_urls=picture_urls,
                        cell_monthly_payment=cell_monthly_payment
                    )
                    products.append(product)

        return products
