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

            soup = BeautifulSoup(session.get(
                'https://www.clarochile.cl/personas/ofertaplanconequipo/'
            ).text, 'html.parser')

            for idx, product_tag in enumerate(soup.findAll('div', 'oferta')):
                product_url = product_tag.find('a')['href']
                discovered_entries[product_url].append({
                    'category_weight': 1,
                    'section_name': 'Equipos',
                    'value': idx + 1
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

        soup = BeautifulSoup(session.get(data_url).text,
                             'html.parser')
        containers = soup.findAll('div', 'new-card') + soup.findAll('div', 'card-box')

        products = []
        portabilidad_modes = [
            '',
            ' Portabilidad',
        ]

        leasing_modes = [
            ' (con cuota de arriendo)',
            ' (sin cuota de arriendo)'
        ]

        for container in soup.findAll('div', 'new-card'):
            plan_name = container.find('span', 'new-card__title').text.strip()
            plan_price = Decimal(remove_words(
                container.findAll('li')[1].text.strip()))

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

        for container in soup.findAll('div', 'card-box'):
            plan_name = container.find('h1').text.strip()
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
        cell_id = url.split('/')[-1]
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        data = 'id={}'.format(cell_id)

        response = session.post(
            'https://equipos.clarochile.cl/servicio/detalle/equipo_plan',
            data=data)

        try:
            product_json = json.loads(response.text)[0]
        except json.decoder.JSONDecodeError:
            return []

        base_cell_name = '{} {} ({})'.format(product_json['marca'],
                                             product_json['modelo_comercial'],
                                             product_json['modelo_tecnico'])

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

                cell_name = '{} - {}'.format(base_cell_name, color)
                base_key = '{} {}'.format(cell_id, color)
                pictures_field = 'sku_{}_img_{}'.format(variant, color_index)
                picture_paths = [path for path in product_json[pictures_field]
                                 if path]
                picture_urls = ['https://equipos.clarochile.cl/adminequipos/'
                                'uploads/equipo/' + path.replace(' ', '%20')
                                for path in picture_paths]

                if cls.include_prepago_price:
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
                            picture_urls=picture_urls,
                            cell_monthly_payment=Decimal(0)
                        )
                        products.append(product)

                for plan_entry in product_json.get('planes', []):
                    plan_id = plan_entry['cat04_plan_id']
                    data = 'id_plan={}&id={}'.format(plan_id,
                                                     product_json['id'])
                    response = session.post(
                        'https://equipos.clarochile.cl/servicio/detalle/'
                        'planes_equipo',
                        data=data, verify=False)
                    plan_data = json.loads(response.text)
                    base_plan_name = plan_data['cat04_plan_nombre']

                    for plan_suffix, price_field, cell_monthly_payment_field \
                            in cls.combinations:
                        plan_name = base_plan_name + plan_suffix

                        if plan_data[price_field]:
                            price = Decimal(remove_words(
                                plan_data[price_field]))
                        else:
                            # Equipo de la otra modalidad (ClaroUp si estamos
                            # scrapeando Claro, Claro si estamos scrapeando
                            # ClaroUp), ver las dos variantes de "combinations"
                            # que hay.
                            # Asegurarse que sea una combinación que tenga
                            # cuota de arriendo
                            assert cell_monthly_payment_field is not None
                            continue

                        if cell_monthly_payment_field:
                            cell_monthly_payment_text = plan_data[
                                cell_monthly_payment_field]
                            if cell_monthly_payment_text:
                                cell_monthly_payment = Decimal(remove_words(
                                    cell_monthly_payment_text))
                            else:
                                # Equipo no tiene la modalidad de pago en
                                # cuotas
                                continue
                        else:
                            # Equipo con pago al contado
                            cell_monthly_payment = Decimal(0)

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
