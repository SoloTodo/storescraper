import json

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Movistar(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 8
    prepago_url = 'http://ww2.movistar.cl/prepago/'
    planes_url = 'https://ww2.movistar.cl/movil/planes-portabilidad/'
    cell_catalog_suffix = ''
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
                           'catalogo.html?limit=1000' + cls.cell_catalog_suffix
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

        plan_containers = soup.findAll('div', 'np-s')

        for plan_container in plan_containers:
            plan_link = plan_container.find('a')
            plan_url = plan_link['href']
            base_plan_name = plan_container.find('h3').text.strip()

            price_text = plan_container.find('span', 'np-s-price-col').find(
                'em').text
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

        if page.url == 'https://catalogo.movistar.cl/equipomasplan/' \
                       'catalogo.html':
            return []

        if page.status_code in [404, 503]:
            return []

        soup = BeautifulSoup(page.text, 'html.parser')
        if soup.find('h1'):
            base_name = soup.find('h1').text.strip()
        else:
            return []

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
                    # Sin arriendo
                    print('porta sin arriendo')

                    payload = 'current%5Bsku%5D={}&current%5Btype%5D=1&' \
                              'current%5Bpayment%5D=1&' \
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
                        price_tag = cell_soup.find('div', {'data-method': '1'})

                        if not price_tag:
                            continue

                        price = Decimal(price_tag['data-price'])
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

                    code = json_response['codeOfferCurrent']
                    cell_url = '{}?codigo={}'.format(base_url, code)
                    cell_soup = BeautifulSoup(session.get(cell_url).text,
                                              'html.parser')
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
                        try:
                            json_response = get_json_response(payload)
                        except Exception:
                            return []

                        for container in json_response['planes']['dataplan']:
                            cell_plan_name = \
                                container['name'] + ' Portabilidad Cuotas'
                            code = container['codigo']
                            cell_url = '{}?codigo={}'.format(base_url, code)
                            print(cell_url)

                            cell_soup = BeautifulSoup(
                                session.get(cell_url).text,
                                'html.parser')
                            price_tag = cell_soup.find('div',
                                                       {'data-method': '2'})

                            if not price_tag:
                                continue

                            price = Decimal(remove_words(price_tag.find(
                                'p', 'boxEMPlan-int-box-pie').contents[1]))
                            cell_monthly_payment = Decimal(remove_words(
                                price_tag.find('p',
                                               'boxEMPlan-int-meses').find(
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
                    # Sin arriendo
                    print('nuevo')

                    payload = 'current%5Bsku%5D={}&current%5Btype%5D=3&' \
                              'current%5Bpayment%5D=1&' \
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
                        price_tag = cell_soup.find('div', {'data-method': '1'})

                        if not price_tag:
                            continue

                        price = Decimal(price_tag['data-price'])

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
