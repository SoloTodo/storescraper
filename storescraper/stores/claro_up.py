import json
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class ClaroUp(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        if category != 'Cell':
            return []

        soup = BeautifulSoup(session.get(
            'https://equipos.clarochile.cl/servicio/catalogo'
        ).text, 'html.parser')

        products_json = json.loads(soup.contents[-1])

        for idx, product_entry in enumerate(products_json):
            product_slug = product_entry['slug']
            product_url = 'https://equipos.clarochile.cl/' \
                          'catalogo/' + product_slug
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        cell_id = url.split('/')[-1]
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        data = 'id={}'.format(cell_id)

        response = session.post(
            'https://equipos.clarochile.cl/servicio/detalle', data=data)

        product_json = json.loads(response.text)[0]

        has_claro_up = int(product_json['claro_up'])

        if not has_claro_up:
            return []

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

            picture_paths = [path for path in product_json[pictures_field]
                             if path]

            picture_urls = ['https://equipos.clarochile.cl/adminequipos/'
                            'uploads/equipo/' + path.replace(' ', '%20')
                            for path in picture_paths]

            base_key = '{} {}'.format(cell_id, color)

            for plan_entry in product_json.get('planes', []):
                plan_name = plan_entry['nombre'] + ' Cuotas'
                price = Decimal(remove_words(plan_entry['claro_up_pie']))
                cell_monthly_payment = Decimal(remove_words(
                    plan_entry['claro_up_cuota']))

                if not cell_monthly_payment:
                    continue

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

            color_index += 1

        return products
