from collections import defaultdict
from decimal import Decimal
from bs4 import BeautifulSoup
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Claro(Store):
    planes_url = 'https://www.clarochile.cl/personas/servicios/' \
                 'servicios-moviles/postpago/planes-y-precios/'
    prepago_url = 'https://www.clarochile.cl/personas/servicios/' \
                  'servicios-moviles/prepago/'
    equipos_url = 'https://www.clarochile.cl/personas/ofertaplanconequipo/'

    combinations = [
        ('', 'valor_contado_planes', None),
        (' Cuotas', 'papcn_pc_valor_cuota_inicial', 'papcn_pc_12_cuotas_de'),
        (' Portabilidad', 'valor_contado_planes', None),
        (' Portabilidad Cuotas', 'pap_pc_valor_cuota_inicial',
         'pap_pc_12_cuotas_de'),
    ]
    include_prepago_price = True

    @classmethod
    def categories(cls):
        return [
            'Cell',
            'CellPlan'
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
        if category == 'Cell':
            discovered_entries[cls.equipos_url].append({
                'category_weight': 1,
                'section_name': 'Equipos',
                'value': 1
            })

        return discovered_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        products = []
        if url == cls.prepago_url:
            # Plan Prepago
            p = Product(
                'Claro Prepago',
                cls.__name__,
                category,
                url,
                url,
                'Claro Prepago',
                -1,
                Decimal(0),
                Decimal(0),
                'CLP',
            )
            products.append(p)
        elif url == cls.planes_url:
            # Plan Postpago
            planes = cls._planes(url, extra_args)
            products.extend(planes)
        elif url == cls.equipos_url:
            # Equipo postpago
            products.extend(cls._celular_postpago(url, extra_args))
        else:
            raise Exception('Invalid URL: ' + url)
        return products

    @classmethod
    def _planes(cls, url, extra_args):
        session = session_with_proxy(extra_args)
        data_url = 'https://digital.clarochile.cl/wcm-inyect/' \
                   'landing-postpago/content.html'

        soup = BeautifulSoup(session.get(data_url).text,
                             'html.parser')

        products = []
        portabilidad_modes = [
            '',
            # ' Portabilidad',
        ]

        leasing_modes = [
            # ' (con cuota de arriendo)',
            ' (sin cuota de arriendo)'
        ]

        # for container in soup.findAll('div', 'new-card'):
        #     plan_name = container.find('span', 'new-card__title')
        #     .text.strip()
        #     plan_price = Decimal(remove_words(
        #         container.findAll('li')[1].text.strip()))
        #
        #     for portability_mode in portabilidad_modes:
        #         for leasing_mode in leasing_modes:
        #             name = '{}{}{}'.format(plan_name, portability_mode,
        #                                    leasing_mode)
        #             key = '{}{}{}'.format(plan_name, portability_mode,
        #                                   leasing_mode)
        #
        #             products.append(Product(
        #                 name,
        #                 cls.__name__,
        #                 'CellPlan',
        #                 url,
        #                 url,
        #                 key,
        #                 -1,
        #                 plan_price,
        #                 plan_price,
        #                 'CLP'))

        for container in soup.findAll('div', 'card-box'):
            plan_name = container.find('h1').text.strip()
            plan_name = ' '.join(plan_name.split())
            plan_price = Decimal(remove_words(container.findAll(
                'h2')[1].text.strip()))

            for portability_mode in portabilidad_modes:
                for leasing_mode in leasing_modes:
                    name = '{}{}{}'.format(plan_name, portability_mode,
                                           leasing_mode)
                    key = '{}{}{}'.format(plan_name, portability_mode,
                                          leasing_mode)

                    products.append(Product(
                        name,
                        cls.__name__,
                        'CellPlan',
                        url,
                        url,
                        key,
                        -1,
                        plan_price,
                        plan_price,
                        'CLP'))

        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        # 1. Obtain cell plans data
        plans = cls._planes(cls.planes_url, extra_args)
        cell_plans_names = ['Claro ' + plan.name.split('(')[0].strip()
                            for plan in plans]

        # 2. Obtain the products
        session = session_with_proxy(extra_args)
        res = session.get('https://www.clarochile.cl/'
                          'personas/ofertaplanconequipo/')
        soup = BeautifulSoup(res.text, 'html.parser')
        products = []

        for cell_tag in soup.findAll('div', 'oferta'):
            cell_name = cell_tag.find('div', 'datos-plan').find(
                'h2').text.strip()
            price_text = cell_tag.find('div', 'cuotas').findAll(
                'i')[-1].text.split('$')[1]
            price = Decimal(remove_words(price_text))
            picture_urls = [cell_tag.find('div', 'imagen-equipo').find(
                'img')['src']]

            for cell_plan_name in cell_plans_names:
                product = Product(
                    cell_name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    '{} - {}'.format(cell_name, cell_plan_name),
                    -1,
                    price,
                    price,
                    'CLP',
                    cell_plan_name=cell_plan_name,
                    picture_urls=picture_urls,
                    cell_monthly_payment=Decimal(0)
                )
                products.append(product)

        return products
