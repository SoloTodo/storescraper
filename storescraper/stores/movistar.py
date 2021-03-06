import json
import re

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Movistar(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 3
    prepago_url = 'http://ww2.movistar.cl/prepago/'
    planes_url = 'https://ww2.movistar.cl/movil/planes-portabilidad/'
    portability_choices = [
        (3, ''),
        (1, ' Portabilidad'),
    ]

    @classmethod
    def categories(cls):
        return [
            'CellPlan',
            'Cell'
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        product_entries = defaultdict(lambda: [])

        if category == 'CellPlan':
            product_entries[cls.prepago_url].append({
                'category_weight': 1,
                'section_name': 'Planes',
                'value': 1
            })

            product_entries[cls.planes_url].append({
                'category_weight': 1,
                'section_name': 'Planes',
                'value': 2
            })
        elif category == 'Cell':
            catalogo_url = 'https://catalogo.movistar.cl/equipomasplan/' \
                           'catalogo.html?limit=1000'
            session = session_with_proxy(extra_args)
            session.headers['user-agent'] = 'python-requests/2.21.0'
            soup = BeautifulSoup(session.get(catalogo_url).text, 'html.parser')
            containers = soup.findAll('li', 'itemsCatalogo')

            if not containers:
                raise Exception('No cells found')

            for idx, container in enumerate(containers):
                product_url = container.find('a')['href']
                if product_url.endswith('?codigo='):
                    continue
                product_entries[product_url].append({
                    'category_weight': 1,
                    'section_name': 'Smartphones',
                    'value': idx + 1
                })

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = []
        if url == cls.prepago_url:
            # Plan Prepago
            p = Product(
                'Movistar Prepago',
                cls.__name__,
                category,
                url,
                url,
                'Movistar Prepago',
                -1,
                Decimal(0),
                Decimal(0),
                'CLP',
            )
            products.append(p)
        elif url == cls.planes_url:
            # Plan Postpago
            products.extend(cls._plans(url, extra_args))
        elif 'catalogo.movistar.cl' in url:
            # Equipo postpago
            products.extend(cls._celular_postpago(url, extra_args))
        else:
            raise Exception('Invalid URL: ' + url)
        return products

    @classmethod
    def _plans(cls, url, extra_args):
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'python-requests/2.21.0'
        soup = BeautifulSoup(session.get(url, timeout=30).text, 'html5lib')
        products = []

        plan_containers = soup.findAll('div', 'mb-parrilla_col')

        for plan_container in plan_containers:
            plan_link = plan_container.find('a')
            plan_url = plan_link['href']

            base_plan_name = 'Plan ' + plan_link.find('h3').text.strip()
            base_plan_name = base_plan_name.replace('&nbsp;', '')

            price_text = plan_container.find('div', 'mb-parrilla_price').find(
                'p', 'price').text
            price = Decimal(remove_words(price_text.split()[0]))

            portability_suffixes = ['', ' Portabilidad']
            cuotas_suffixes = [
                ' (sin cuota de arriendo)',
                ' (con cuota de arriendo)'
            ]

            for portability_suffix in portability_suffixes:
                for cuota_suffix in cuotas_suffixes:
                    plan_name = '{}{}{}'.format(
                        base_plan_name, portability_suffix, cuota_suffix)

                    products.append(Product(
                        plan_name,
                        cls.__name__,
                        'CellPlan',
                        plan_url,
                        url,
                        plan_name,
                        -1,
                        price,
                        price,
                        'CLP'
                    ))

        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'python-requests/2.21.0'
        ajax_session = session_with_proxy(extra_args)
        ajax_session.headers['Content-Type'] = \
            'application/x-www-form-urlencoded'
        ajax_session.headers['user-agent'] = 'python-requests/2.21.0'
        ajax_session.headers['x-requested-with'] = 'XMLHttpRequest'
        page = session.get(url)

        if page.status_code == 404:
            return []

        soup = BeautifulSoup(page.text, 'html.parser')
        base_name = soup.find('h1').text.strip()

        is_movistar_one = soup.find('p', text='+ cuotas Movistar One')

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

        if is_movistar_one:
            payload_params = 'current%5BhasMovistar1%5D=1&' \
                             'current%5Bmovistar1%5D=1'
        else:
            payload_params = ''

        for sku, color_id, color_name in sku_color_choices:
            name = '{} {}'.format(base_name, color_name)

            for portability_type_id, portability_suffix in \
                    cls.portability_choices:

                if portability_type_id == 1:
                    # Portabilidad
                    # Sin arriendo
                    print('porta sin arriendo')

                    payload = 'current%5Bsku%5D={}&current%5Btype%5D=1&' \
                              'current%5Bpayment%5D=1&' \
                              'current%5Bplan%5D=Plus+Libre+Cod_0J3_Porta' \
                              '&{}&current%5Bcode%5D=' \
                              ''.format(sku, payload_params)
                    json_response = get_json_response(payload)
                    code = json_response['codeOfferCurrent']

                    cell_url = '{}?codigo={}'.format(base_url, code)
                    print(cell_url)

                    cell_soup = BeautifulSoup(session.get(cell_url).text,
                                              'html.parser')
                    json_soup = BeautifulSoup(json_response['planes']['html'],
                                              'html.parser')

                    price_container = cell_soup.find(
                        'div', 'boxEMPlan-int-costo-0')

                    # Movistar one phones do not have this pricing option
                    if price_container:
                        price_container_text = price_container.findAll(
                            'b')[1].text
                        monthly_price = Decimal(
                            re.search(r'\$([\d+.]+)',
                                      price_container_text
                                      ).groups()[0].replace('.', ''))
                        price = 24 * monthly_price

                        for container in json_soup.findAll('article'):
                            cell_plan_name = container['data-id']

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
                                cell_monthly_payment=Decimal(0)
                            ))

                    # Con arriendo

                    has_arriendo_option = cell_soup.find(
                        'li', {'id': 'metodo2'})

                    if has_arriendo_option:
                        print('Porta con arriendo')
                        payload = 'current%5Bsku%5D={}&current%5Btype%5D=1&' \
                                  'current%5Bpayment%5D=2&' \
                                  'current%5Bplan%5D=' \
                                  'Plus+Libre+Cod_0J3_Porta' \
                                  '&{}&current%5Bcode%5D=' \
                                  ''.format(sku, payload_params)
                        json_response = get_json_response(payload)
                        json_soup = BeautifulSoup(
                            json_response['planes']['html'],
                            'html5lib')
                        plan_containers = json_soup.findAll('article')

                        for container in plan_containers:
                            cell_plan_name = container['data-id']
                            price = Decimal(remove_words(container.find(
                                'strong', 'pie-price').text))

                            monthly_payment_text = container.find(
                                'div', 'pie-detail').findAll('strong')[-1].text
                            monthly_payment_text = re.search(
                                r'\$([\d+.]+)',
                                monthly_payment_text).groups()[0]
                            cell_monthly_payment = Decimal(
                                monthly_payment_text.replace('.', ''))

                            products.append(Product(
                                name,
                                cls.__name__,
                                'Cell',
                                cell_url,
                                cell_url,
                                '{} - {} - {} cuotas'.format(sku, color_id,
                                                             cell_plan_name),
                                -1,
                                price,
                                price,
                                'CLP',
                                cell_plan_name='{} cuotas'.format(
                                    cell_plan_name),
                                cell_monthly_payment=cell_monthly_payment
                            ))
                elif portability_type_id == 3:
                    # Nuevo
                    # Sin arriendo
                    print('nuevo')

                    payload = 'current%5Bsku%5D={}&current%5Btype%5D=3&' \
                              'current%5Bpayment%5D=1&' \
                              'current%5Bplan%5D=&current%5Bmovistar1%5D=0&' \
                              '{}&current%5Bcode%5D=' \
                              ''.format(sku, payload_params)
                    json_response = get_json_response(payload)
                    code = json_response['codeOfferCurrent']

                    cell_url = '{}?codigo={}'.format(base_url, code)
                    print(cell_url)

                    cell_soup = BeautifulSoup(session.get(cell_url).text,
                                              'html.parser')
                    json_soup = BeautifulSoup(json_response['planes']['html'],
                                              'html.parser')

                    price_container = cell_soup.find(
                        'div', 'boxEMPlan-int-costo-0')

                    # Movistar one only phones do not have this option
                    if price_container:
                        price_container_text = price_container.findAll(
                            'b')[1].text
                        monthly_price = Decimal(
                            re.search(r'\$([\d+.]+)',
                                      price_container_text
                                      ).groups()[0].replace('.', '')
                        )
                        price = 24 * monthly_price

                        for container in json_soup.findAll('article'):
                            # break
                            cell_plan_name = container['data-id']

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
                                cell_monthly_payment=Decimal(0)
                            ))

        return products
