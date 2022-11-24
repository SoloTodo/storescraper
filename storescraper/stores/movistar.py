import base64
import json

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, trim


class Movistar(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 8
    prepago_url = 'http://ww2.movistar.cl/prepago/'
    planes_url = 'https://ww2.movistar.cl/movil/planes-portabilidad/'
    cell_catalog_suffix = ''
    # Format: (type, payment, suffix)
    # type 1 (Portabilidad), 3 (Linea nueva)
    # payment 1 (Sin arriendo), 2 (Cuotas), 3 (Movistar One)
    aquisition_options = [
        # Línea nueva sin arriendo
        (3, 1, ''),
        # Portabilidad sin arriendo
        (1, 1, ' Portabilidad'),
        # Portabilidad con arriendo
        (1, 2, ' Portabilidad Cuotas'),
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
            page = 1
            idx = 1

            while True:
                if page >= 30:
                    raise Exception('Page overflow')

                catalogo_url = 'https://catalogo.movistar.cl/equipomasplan/' \
                               'catalogo.html?p={}'.format(page) + \
                    cls.cell_catalog_suffix
                print(catalogo_url)
                session = session_with_proxy(extra_args)
                session.headers['user-agent'] = 'python-requests/2.21.0'
                soup = BeautifulSoup(session.get(
                    catalogo_url).text, 'html.parser')
                containers = soup.findAll('div', 'itemsCatalogo')

                if not containers:
                    if page == 1:
                        raise Exception('No cells found')
                    break

                for container in containers:
                    product_url = container.find('a')['href']
                    if product_url in product_entries:
                        print(product_url)
                    product_entries[product_url].append({
                        'category_weight': 1,
                        'section_name': 'Smartphones',
                        'value': idx
                    })
                    idx += 1
                page += 1

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

        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        products = []

        for color_container in soup.find('ul', 'colorEMP').findAll('li'):
            color_element = color_container.find('a')
            sku_url = color_element['data-url-key']
            products.extend(cls.__celular_postpago(sku_url, extra_args))

        return products

    @classmethod
    def __celular_postpago(cls, url, extra_args):
        print(url)

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'python-requests/2.21.0'
        ajax_session = session_with_proxy(extra_args)
        ajax_session.headers['Content-Type'] = \
            'application/x-www-form-urlencoded'
        ajax_session.headers['user-agent'] = 'python-requests/2.21.0'
        ajax_session.headers['x-requested-with'] = 'XMLHttpRequest'
        del ajax_session.headers['Accept-Encoding']
        page = session.get(url)

        if page.url == 'https://catalogo.movistar.cl/equipomasplan/' \
                       'catalogo.html':
            raise Exception('Catalogo page URL')

        if page.status_code in [404, 503]:
            raise Exception('Invalid status code: ' + str(page.status_code))

        soup = BeautifulSoup(page.text, 'html.parser')
        if soup.find('meta', {'name': 'title'}):
            name = soup.find('meta', {'name': 'title'})['content']
        else:
            raise Exception('No base name found')

        products = []
        base_url = url.split('?')[0]

        def get_json_response(_payload):
            print(_payload)
            if 'Cookie' in ajax_session.headers:
                del ajax_session.headers['Cookie']
            # print(ajax_session.headers)
            _response = ajax_session.post(
                'https://catalogo.movistar.cl/equipomasplan/'
                'emp_detalle/planes',
                data=_payload)
            # import curlify; print(curlify.to_curl(_response.request))

            return json.loads(_response.text)

        payload_params = 'current%5BhasMovistar1%5D=1&' \
                         'current%5Bmovistar1%5D=0'

        status_tag = soup.find('div', 'current-status')
        skus = {
            'contado': status_tag['data-sku'],
            'cuotas': status_tag['data-code']
        }

        movistar_one_tag = soup.select('div.boxEMPlan.metodo3.visible')
        if movistar_one_tag:
            # This SKU should only be needed for movistar one enabled SKUs
            skus['movistar_one'] = movistar_one_tag[0]['data-code']

        for type_id, payment_id, suffix in cls.aquisition_options:
            if payment_id == 1:
                sku_to_use = skus['contado']
            elif payment_id == 2:
                sku_to_use = skus['cuotas']
            elif payment_id == 3:
                if 'movistar_one' not in skus:
                    # This can happen if the original product is available
                    # with movistar one, but we are scraping a color variant
                    # of it that is not
                    continue
                sku_to_use = skus['movistar_one']
            else:
                raise Exception('Invalid payment ID')

            payload = 'current%5Bsku%5D={}&current%5Btype%5D={}&' \
                      'current%5Bpayment%5D={}&' \
                      'current%5Bplan%5D=' \
                      'Movistar+con+Todo+Libre+Cod_0P8_Porta' \
                      '&{}&current%5Bcode%5D=' \
                      ''.format(sku_to_use, type_id, payment_id, payload_params)

            json_response = get_json_response(payload)

            for container in json_response['planes']['dataplan']:
                cell_plan_name = trim(container['name']) + suffix
                code = container['codigo']
                b64code = base64.b64encode(
                    code.encode('utf-8')).decode('utf-8')
                cell_url = '{}?codigo={}'.format(base_url, b64code)
                print(cell_url)

                cell_soup = BeautifulSoup(session.get(cell_url).text,
                                          'html.parser')
                if payment_id == 1:
                    price_tag = cell_soup.find('div', {'data-method': '1'})
                    price = Decimal(price_tag['data-price']).quantize(0)
                    cell_monthly_payment = Decimal(0)
                elif payment_id == 2:
                    price_tag = cell_soup.find('div', {'data-method': '2'})
                    price = Decimal(remove_words(price_tag.find(
                        'p', 'boxEMPlan-int-box-pie').contents[1]))
                    cell_monthly_payment = Decimal(remove_words(
                        price_tag.find('p',
                                       'boxEMPlan-int-meses').find(
                            'b').text))
                elif payment_id == 3:
                    price_tag = cell_soup.find('div', {'data-method': '3'})
                    price = Decimal(price_tag['data-price']).quantize(0)
                    cell_monthly_payment = Decimal(0)
                else:
                    raise Exception('Invalid payment ID')

                products.append(Product(
                    name,
                    cls.__name__,
                    'Cell',
                    cell_url,
                    cell_url,
                    '{} - {}'.format(sku_to_use, cell_plan_name),
                    -1,
                    price,
                    price,
                    'CLP',
                    cell_plan_name=cell_plan_name,
                    cell_monthly_payment=cell_monthly_payment
                ))

        return products
