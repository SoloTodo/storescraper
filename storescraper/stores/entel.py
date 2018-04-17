import json

import time
from bs4 import BeautifulSoup
from decimal import Decimal

from selenium import webdriver

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
            for path in ['index.iws', 'index2.iws']:
                plan_url = 'http://www.entel.cl/planes/' + path
                product_urls.append(plan_url)

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

            # # Plan PVP (compra equipo sin cuota de arriendo)
            # products.append(Product(
            #     'Entel PVP',
            #     cls.__name__,
            #     category,
            #     url,
            #     url,
            #     'Entel PVP',
            #     -1,
            #     Decimal(0),
            #     Decimal(0),
            #     'CLP',
            # ))
            #
            # # Plan PVP Portabilidad (compra equipo en portabilidad sin cuota
            # # de arriendo)
            # products.append(Product(
            #     'Entel PVP Portabilidad',
            #     cls.__name__,
            #     category,
            #     url,
            #     url,
            #     'Entel PVP Portabilidad',
            #     -1,
            #     Decimal(0),
            #     Decimal(0),
            #     'CLP',
            # ))
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
        driver = webdriver.PhantomJS()

        tries = 1

        while True:
            if tries >= 10:
                raise Exception('Try overflow getting plans')
            print('Try: {}'.format(tries))
            driver.get(url)
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            plan_tabs = soup.findAll('div', 'align-left')
            if plan_tabs:
                break

            tries += 1

        products = []

        for plan_tab in plan_tabs:
            base_plan_name = plan_tab.find('h5').text.strip()

            print(base_plan_name)

            for suffix in ['', ' Portabilidad']:
                name = base_plan_name + suffix

                normal_price_container = plan_tab.find(
                    'p', 'valor-dcto-caja-precio')

                highlighted_price = Decimal(remove_words(
                    plan_tab.find('p', 'monto').text))

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

        driver.close()
        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        print(url)
        session = session_with_proxy(extra_args)
        slug = url.split('/')[-1]

        details_url = 'https://equipos.entel.cl/device/{}.json'.format(slug)

        print(details_url)

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
                 'sale_price_promotion'),
                (' Portabilidad',
                 ('portability_price_promotion', 'price_1'),
                 'portability_price'),
            ]

            # pvp_price = None
            # pvp_portability_price = Decimal('Infinity')

            # Use the prices of the first variant with the same capacity
            for plan in pricing_variant['plans']:
                plan = plan['plan']

                if plan['plan_type'] in ['cargo_fijo', 'voz',
                                         'multi_smart',
                                         'cuenta_controlada']:
                    continue

                if plan['modality'] != 'contratacion':
                    continue

                # if pvp_price and pvp_price != Decimal(plan['sale_price']):
                #     raise Exception('Mismatch sale price')
                #
                # pvp_price = Decimal(plan['sale_price'])
                #
                # if plan['title'] in ['Libre 30GB', 'Controlado 7GB'] and
                # plan['discount_percentage']:
                #     listed_pvp_portability_price = Decimal(
                #         plan['discount_percentage'])
                #
                #     if listed_pvp_portability_price < pvp_portability_price:
                #         pvp_portability_price = listed_pvp_portability_price

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

                    products.append(Product(
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
                    ))

            # products.append(Product(
            #     variant_name,
            #     cls.__name__,
            #     'Cell',
            #     url,
            #     url,
            #     '{} - Entel PVP'.format(variant_name),
            #     -1,
            #     pvp_price,
            #     pvp_price,
            #     'CLP',
            #     cell_plan_name='Entel PVP',
            #     picture_urls=picture_urls,
            #     cell_monthly_payment=Decimal(0)
            # ))
            #
            # if pvp_portability_price.is_finite():
            #     products.append(Product(
            #         variant_name,
            #         cls.__name__,
            #         'Cell',
            #         url,
            #         url,
            #         '{} - Entel PVP Portabilidad'.format(variant_name),
            #         -1,
            #         pvp_portability_price,
            #         pvp_portability_price,
            #         'CLP',
            #         cell_plan_name='Entel PVP Portabilidad',
            #         picture_urls=picture_urls,
            #         cell_monthly_payment=Decimal(0)
            #     ))

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
