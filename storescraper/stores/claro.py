import json

import re
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Claro(Store):
    planes_url = 'http://www.clarochile.cl/personas/servicios/' \
                 'servicios-moviles/postpago/planes-y-precios/'
    prepago_url = 'http://www.clarochile.cl/personas/servicios/' \
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
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        if category == 'CellPlan':
            product_urls.append(cls.prepago_url)

            page_source = session.get(cls.planes_url).text

            plan_data_raw_json = re.search(
                r'jsonPlanes.*\'(\[.*)',
                page_source).groups()[0].split('\'')[0]

            plan_data_json = json.loads(plan_data_raw_json)

            for plan_entry in plan_data_json:
                plan_id = plan_entry['fi_plan']
                for suffix, field_name, sku_suffix in cls.plan_variations:
                    if sku_suffix:
                        sku = '{}_{}'.format(plan_id, sku_suffix)
                    else:
                        sku = plan_id

                    plan_url = 'http://www.clarochile.cl/personas/servicios/' \
                               'servicios-moviles/postpago/planes-y-precios/' \
                               '{}/'.format(sku)
                    product_urls.append(plan_url)

        if category == 'Cell':
            # Con plan

            products_json = json.loads(session.get(
                'https://equipos.clarochile.cl/servicio/catalogo'
            ).text)

            for idx, product_entry in enumerate(products_json):
                product_id = product_entry['id']
                product_url = 'https://equipos.clarochile.cl/' \
                              'detalle.html?id=' + product_id
                product_urls.append(product_url)

        return product_urls

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
        elif 'planes-y-precios' in url:
            # Plan Postpago
            products.append(cls._plan(url, extra_args))
        elif 'equipos.clarochile.cl' in url:
            # Equipo postpago
            products.extend(cls._celular_postpago(url, extra_args))
        else:
            raise Exception('Invalid URL: ' + url)
        return products

    @classmethod
    def _plan(cls, url, extra_args):
        variation_code_to_suffix = {e[2]: e[0] for e in cls.plan_variations}

        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        sku = [e for e in url.split('/') if e][-1]

        sku_parts = sku.split('_')
        if len(sku_parts) == 1:
            variation_code = ''
        else:
            variation_code = sku_parts[1]

        assert variation_code in variation_code_to_suffix

        pricing_container = soup.find('section', 'detallePlan')

        name = pricing_container.find('h3').text.strip() + \
            variation_code_to_suffix[variation_code]

        normal_price = Decimal(remove_words(
            pricing_container.find('h2').text.replace('Mensuales', '')))
        offer_price = normal_price

        description = html_to_markdown(
            str(soup.find('div', {'id': 'contenedorPrincipal'})))

        product = Product(
            name,
            cls.__name__,
            'CellPlan',
            url,
            url,
            sku,
            -1,
            normal_price,
            offer_price,
            'CLP',
            description=description
        )

        return product

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        query_string = urllib.parse.urlparse(url).query
        cell_id = urllib.parse.parse_qs(query_string)['id'][0]
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        data = 'id={}'.format(cell_id)

        response = session.post(
            'https://equipos.clarochile.cl/servicio/detalle', data=data)

        product_json = json.loads(response.text)[0]

        base_cell_name = '{} {}'.format(product_json['marca'],
                                        product_json['modelo_comercial'])

        products = []

        color_index = 1
        while True:
            field_name = 'sku_prepago_color_{}'.format(color_index)
            pictures_field = 'sku_prepago_img_{}'.format(color_index)

            color = product_json.get(field_name, None)

            if not color:
                field_name = 'sku_pospago_color_{}'.format(color_index)
                pictures_field = 'sku_pospago_img_{}'.format(color_index)

                color = product_json.get(field_name, None)

                if not color:
                    break

            cell_name = '{} {}'.format(base_cell_name, color)

            prepago_price = Decimal(remove_words(
                product_json['precio_prepago']))

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

                variants = [
                    ('', 'cuota_inicial'),
                    (' Portabilidad', 'cuota_inicial_portado')
                ]

                for suffix, field_name in variants:
                    price = remove_words(plan_entry[field_name])

                    if price == '-':
                        continue

                    price = Decimal(price)

                    plan_name = base_plan_name + suffix

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
                        picture_urls=picture_urls
                    )
                    products.append(product)

            color_index += 1

        return products
