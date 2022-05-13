import json
from collections import defaultdict
from decimal import Decimal

import demjson
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
            cell_urls = cls._discover_cells(extra_args)
            for idx, cell_url in enumerate(cell_urls):
                discovered_entries[cell_url].append({
                    'category_weight': 1,
                    'section_name': 'Equipos',
                    'value': idx + 1
                })

        return discovered_entries

    @classmethod
    def _discover_cells(cls, extra_args=None):
        product_urls = []
        session = session_with_proxy(extra_args)
        offset = 0

        while True:
            category_url = 'https://tienda.clarochile.cl/CategoryDisplay' \
                           '?facet_1=ads_f11503_ntk_cs%3A%22Portando+un' \
                           '+Plan%22&categoryId=3074457345616686668&' \
                           'storeId=10151&beginIndex={}'.format(offset)
            print(category_url)
            soup = BeautifulSoup(
                session.get(category_url, verify=False).text,
                'html5lib'
            )

            containers = soup.find(
                'div', 'product_listing_container').findAll(
                'div', 'product')[1:]

            if not containers:
                if offset == 0:
                    raise Exception('Empty list')

                break

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

            offset += 12

        return product_urls

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
        else:
            # Celular
            cells = cls._celular_postpago(url, extra_args)
            products.extend(cells)
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
            ' Portabilidad',
        ]

        leasing_modes = [
            ' (sin cuota de arriendo)',
            ' (con cuota de arriendo)'
        ]

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
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url, verify=False)
        soup = BeautifulSoup(res.text, 'html5lib')
        product_id = soup.find('meta', {'name': 'pageId'})['content']
        base_name = soup.find('h1', 'main_header').text.strip()
        picture_tag_id = 'ProductInfoImage_' + product_id
        picture_urls = ['https://tienda.clarochile.cl' +
                        soup.find('input', {'id': picture_tag_id})['value']
                        .replace(' ', '%20')]

        category_entries_tag = soup.find(
            'div', {'id': 'entitledItem_' + product_id})
        category_entries = json.loads(
            category_entries_tag.text.replace('\'', '\"'))

        session.headers['Content-Type'] = 'application/x-www-form-urlencoded' \
                                          '; charset=UTF-8'
        products = []

        for c in category_entries:
            payload = 'storeId=10151&langId=-5' \
                      '&catalogId=10052&catalogEntryId={}' \
                      '&productId={}&requesttype=ajax'.format(
                          c['catentry_id'], product_id)
            res = session.post(
                'https://tienda.clarochile.cl/GetCatalogEntryDetailsByIDView',
                payload)
            data = demjson.decode(res.text)['catalogEntry']

            combination_type = data['attrSwatchFlujo']

            if combination_type in ['REB', 'RET', '']:
                # Renovación or Default
                continue

            priceText = remove_words(data['offerPrice'])
            if not priceText:
                return []
            price = Decimal(priceText)

            attributes = []
            for key, value in c['Attributes'].items():
                attr_label, attr_value = key.split('_|_')
                if attr_label == 'Flujo':
                    continue
                attributes.append('{} {}'.format(attr_label, attr_value))

            name = '{} ({})'.format(base_name, ' / '.join(attributes))

            if combination_type == 'PRE':
                # Prepago
                products.append(Product(
                    name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    '{} - {}'.format(product_id, 'Claro Prepago'),
                    -1,
                    price,
                    price,
                    'CLP',
                    cell_plan_name='Claro Prepago',
                    picture_urls=picture_urls
                ))
            elif combination_type == 'PE_LN':
                # Línea nueva

                for plan_entry in data['planAssociate']:
                    cell_plan_name = plan_entry['name']

                    products.append(Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} - {}'.format(product_id, cell_plan_name),
                        -1,
                        price,
                        price,
                        'CLP',
                        cell_plan_name='Claro {}'.format(cell_plan_name),
                        cell_monthly_payment=Decimal(0),
                        picture_urls=picture_urls
                    ))
            elif combination_type == 'PEB':
                # Portabildiad arriendo
                if data['catentry_field2'] == "":
                    continue
                num_cuotas = Decimal(data['catentry_field2'])
                cell_monthly_payment = (price / num_cuotas).quantize(0)

                for plan_entry in data['planAssociate']:
                    cell_plan_name = plan_entry['name'] + \
                        ' Portabilidad Cuotas'

                    products.append(Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} - {}'.format(product_id, cell_plan_name),
                        -1,
                        Decimal(0),
                        Decimal(0),
                        'CLP',
                        cell_plan_name='Claro {}'.format(cell_plan_name),
                        cell_monthly_payment=cell_monthly_payment,
                        picture_urls=picture_urls
                    ))
            elif combination_type == 'PE_PORTA':
                # Portabildiad sin arriendo

                for plan_entry in data['planAssociate']:
                    cell_plan_name = plan_entry['name'] + ' Portabilidad'

                    products.append(Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} - {}'.format(product_id, cell_plan_name),
                        -1,
                        price,
                        price,
                        'CLP',
                        cell_plan_name='Claro {}'.format(cell_plan_name),
                        cell_monthly_payment=Decimal(0),
                        picture_urls=picture_urls
                    ))
            else:
                raise Exception('Invalid switch:' + combination_type)

        return products
