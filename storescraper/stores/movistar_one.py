import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL
from .movistar import Movistar
from ..product import Product
from ..utils import session_with_proxy, remove_words


class MovistarOne(Movistar):
    cell_catalog_suffix = '&movistarone=1'
    default_payment_id = 3

    @classmethod
    def categories(cls):
        return [
            CELL
        ]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'python-requests/2.21.0'
        ajax_session = session_with_proxy(extra_args)
        ajax_session.headers['Content-Type'] = \
            'application/x-www-form-urlencoded'
        ajax_session.headers['user-agent'] = 'python-requests/2.21.0'
        ajax_session.headers['x-requested-with'] = 'XMLHttpRequest'
        page = session.get(url)

        if page.url == 'https://catalogo.movistar.cl/equipomasplan/' \
                       'catalogo.html':
            return []

        if page.status_code in [404, 503]:
            return []

        soup = BeautifulSoup(page.text, 'html.parser')
        base_name = soup.find('h1').text.strip()

        sku_color_choices = []
        for color_container in soup.find('ul', 'colorEMP').findAll('li'):
            color_element = color_container.find('a')
            sku = color_element['data-sku']
            color_id = color_element['data-id']
            color_name = color_element['data-nombre-color']
            sku_color_choices.append((sku, color_id, color_name))

        products = []

        base_url = url.split('?')[0]

        def get_json_response(_payload):
            print(_payload)
            _response = ajax_session.post(
                'https://catalogo.movistar.cl/equipomasplan/'
                'emp_detalle/planes',
                data=_payload)

            return json.loads(_response.text)

        payload_params = 'current%5BhasMovistar1%5D=1&' \
                         'current%5Bmovistar1%5D=0'

        for sku, color_id, color_name in sku_color_choices:
            name = '{} {}'.format(base_name, color_name)

            for portability_type_id, portability_suffix in \
                    cls.portability_choices:

                if portability_type_id == 1:
                    # Portabilidad
                    # Con arriendo
                    print('porta sin arriendo')

                    payload = 'current%5Bsku%5D={}&current%5Btype%5D=1&' \
                              'current%5Bpayment%5D=3&' \
                              'current%5Bplan%5D=' \
                              'Movistar+con+Todo+Libre+Cod_0P8_Porta' \
                              '&{}&current%5Bcode%5D=' \
                              ''.format(sku, payload_params)
                    try:
                        json_response = get_json_response(payload)
                    except Exception:
                        return []

                    for container in json_response['planes']['dataplan']:
                        cell_plan_name = container['name'] + ' Portabilidad'
                        code = container['codigo']
                        cell_url = '{}?codigo={}'.format(base_url, code)
                        print(cell_url)

                        cell_soup = BeautifulSoup(session.get(cell_url).text,
                                                  'html.parser')
                        price_tag = cell_soup.find('div', {'data-method': '3'})

                        price = Decimal(remove_words(price_tag.find(
                            'p', 'boxEMPlan-int-box-pie').contents[1]))
                        cell_monthly_payment = Decimal(remove_words(
                            price_tag.find('p', 'boxEMPlan-int-meses').find(
                                'b').text))

                        products.append(Product(
                            name,
                            cls.__name__,
                            'Cell',
                            cell_url,
                            cell_url,
                            '{} - {} - {}'.format(sku, color_id,
                                                  cell_plan_name),
                            -1,
                            price,
                            price,
                            'CLP',
                            cell_plan_name='{}'.format(cell_plan_name),
                            cell_monthly_payment=cell_monthly_payment
                        ))
                elif portability_type_id == 3:
                    # Nuevo
                    # Con arriendo
                    print('nuevo')

                    payload = 'current%5Bsku%5D={}&current%5Btype%5D=3&' \
                              'current%5Bpayment%5D=3&' \
                              'current%5Bplan%5D=&' \
                              '{}&current%5Bcode%5D=' \
                              ''.format(sku, payload_params)
                    try:
                        json_response = get_json_response(payload)
                    except Exception:
                        return []

                    for container in json_response['planes']['dataplan']:
                        cell_plan_name = container['name']
                        code = container['codigo']
                        cell_url = '{}?codigo={}'.format(base_url, code)
                        print(cell_url)

                        cell_soup = BeautifulSoup(session.get(cell_url).text,
                                                  'html.parser')
                        price_tag = cell_soup.find('div', {'data-method': '3'})

                        price = Decimal(remove_words(price_tag.find(
                            'p', 'boxEMPlan-int-box-pie').contents[1]))
                        cell_monthly_payment = Decimal(remove_words(
                            price_tag.find('p', 'boxEMPlan-int-meses').find(
                                'b').text))

                        products.append(Product(
                            name,
                            cls.__name__,
                            'Cell',
                            cell_url,
                            cell_url,
                            '{} - {} - {}'.format(sku, color_id,
                                                  cell_plan_name),
                            -1,
                            price,
                            price,
                            'CLP',
                            cell_plan_name='{}'.format(cell_plan_name),
                            cell_monthly_payment=cell_monthly_payment
                        ))

        return products
