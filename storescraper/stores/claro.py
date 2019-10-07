import json
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
    plan_variations = [
        ('', 'fi_precio', ''),
        (' Sin Equipo', 'fi_precio_television_espn', 'ESPN'),
        (' Portabilidad', 'fi_precio_telefonia_enps', 'ENPS'),
        (' Portabilidad Sin Equipo', 'fi_precio_internet_esps', 'ESPS'),
    ]

    @classmethod
    def categories(cls):
        return [
            'Cell',
            'CellPlan'
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
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
            # Con plan

            soup = BeautifulSoup(session.post(
                'https://equipos.clarochile.cl/servicio/catalogo',
                'destacados=destacado'
            ).text, 'html.parser')

            products_json = json.loads(soup.contents[-1])

            for idx, product_entry in enumerate(products_json):
                product_slug = product_entry['slug']
                product_url = 'https://equipos.clarochile.cl/' \
                              'catalogo/' + product_slug
                discovered_entries[product_url].append({
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
        elif 'equipos.clarochile.cl' in url:
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

        soup = BeautifulSoup(session.get(data_url).text, 'html.parser')
        containers = soup.findAll('article', 'plan-destacado-Landing')

        products = []
        portabilidad_modes = [
            '',
            ' Portabilidad',
        ]

        leasing_modes = [
            ' (con cuota de arriendo)',
            ' (sin cuota de arriendo)'
        ]

        for container in containers:
            c = container.find('div', 'tab-content').find('div')
            plan_name = c.find('h1').text.strip()
            plan_price_text = c.findAll('h2')[-1]\
                .text.replace('$', '')
            plan_price = Decimal(plan_price_text.replace('.', ''))

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
        cell_id = url.split('/')[-1]
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        data = 'id={}'.format(cell_id)

        response = session.post(
            'https://equipos.clarochile.cl/servicio/detalle', data=data)

        product_json = json.loads(response.text)[0]
        base_cell_name = '{} {}'.format(product_json['marca'],
                                        product_json['modelo_comercial'])

        products = []

        for variant in ['prepago', 'pospago']:
            color_index = 0
            while color_index < 10:
                color_index += 1
                field_name = 'sku_{}_color_{}'.format(variant, color_index)

                color = product_json.get(field_name, None)

                if not color:
                    continue

                sku_field = 'sku_{}_{}'.format(variant, color_index)
                sku = product_json[sku_field]

                if sku == '70004672':
                    color = 'ceramic white'

                cell_name = '{} {}'.format(base_cell_name, color)

                prepago_price = None

                prepago_fields = [
                    'precio_tienda_web',
                    'precio_oferta_prepago',
                    'precio_prepago_normal'
                ]

                for prepago_field in prepago_fields:
                    prepago_price = Decimal(remove_words(
                        product_json[prepago_field]))
                    if prepago_price:
                        break

                pictures_field = 'sku_{}_img_{}'.format(variant, color_index)
                picture_paths = [path for path in product_json[pictures_field]
                                 if path]

                picture_urls = ['https://equipos.clarochile.cl/adminequipos/'
                                'uploads/equipo/' + path.replace(' ', '%20')
                                for path in picture_paths]

                base_key = '{} {}'.format(cell_id, color)

                if prepago_price:
                    product = Product(
                        cell_name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        base_key + ' Claro Prepago',
                        -1,
                        prepago_price,
                        prepago_price,
                        'CLP',
                        cell_plan_name='Claro Prepago',
                        picture_urls=picture_urls
                    )
                    products.append(product)

                for plan_entry in product_json.get('planes', []):
                    base_plan_name = plan_entry['nombre']

                    for suffix in ['', ' Portabilidad']:
                        plan_name = base_plan_name + suffix

                        if suffix:
                            # Portabilidad

                            if int(product_json['postpago_cuotas_view']):
                                # Con cuota mensual de arriendo
                                cell_monthly_payment = Decimal(remove_words(
                                    plan_entry[
                                        'valor_cuota_mensual_portabilidad']))
                                price = Decimal(remove_words(
                                    plan_entry['valor_pie']))
                                plan_name += ' Cuotas'
                            else:
                                # Sin cuota mensual de arriendo
                                cell_monthly_payment = Decimal(0)
                                price = Decimal(remove_words(
                                    plan_entry['cuota_inicial_portado']))
                        else:
                            cell_monthly_payment = Decimal(0)
                            price = Decimal(remove_words(
                                plan_entry['cuota_inicial']))

                        price = Decimal(price)

                        product = Product(
                            cell_name,
                            cls.__name__,
                            'Cell',
                            url,
                            url,
                            '{} - {}'.format(base_key, plan_name),
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
