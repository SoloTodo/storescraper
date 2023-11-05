import logging
import re
import time
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CELL_PLAN, CELL
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Movistar(Store):
    preferred_discover_urls_concurrency = 1
    prepago_url = 'http://ww2.movistar.cl/prepago/'
    planes_url = 'https://ww2.movistar.cl/movil/planes-portabilidad/'
    variations = [{
            'base_plan': 'skuLineaNuevaTienda',
            'methods': [
                (1, ''),
            ]
        },
        {
            'base_plan': 'skuPortabilidadTienda',
            'methods': [
                (1, ' Portabilidad'),
                (2, ' Portabilidad Cuotas'),
            ]}
    ]
    include_prepago = True
    category_paths = [
        ('celulares', CELL),
    ]

    @classmethod
    def categories(cls):
        return [
            CELL_PLAN,
            CELL
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_entries = []

        if category == CELL_PLAN:
            time.sleep(5)
            product_entries.append(cls.prepago_url)
            product_entries.append(cls.planes_url)
        else:
            for category_path, local_category in cls.category_paths:
                if local_category != category:
                    continue

                page = 1

                while True:
                    if page >= 30:
                        raise Exception('Page overflow')

                    catalogo_url = ('https://catalogo.movistar.cl/tienda/{}'
                                    '?p={}&prfilter_ajax=1').format(
                        category_path, page)
                    print(catalogo_url)
                    session = session_with_proxy(extra_args)
                    session.headers['user-agent'] = 'python-requests/2.21.0'
                    soup = BeautifulSoup(session.get(
                        catalogo_url).json()['productlist'], 'html.parser')
                    containers = soup.findAll('li', 'product')

                    if not containers:
                        if page == 1:
                            logging.warning('Empty category: ' + catalogo_url)
                        break

                    for container in containers:
                        product_url = container.find('a')['href'].split('?')[0]
                        print(product_url)

                        product_entries.append(product_url)

                        if len(container.findAll('div', 'color-label')) > 1:
                            product_soup = BeautifulSoup(
                                session.get(product_url).text, 'html.parser')

                            color_list = product_soup.findAll(
                                'li', 'selectOptions-listOptions-list')

                            for color_element in color_list:
                                sku_url = color_element['data-url']
                                if sku_url in product_entries:
                                    continue
                                product_entries.append(sku_url)
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
                allow_zero_prices=True
            )
            products.append(p)
        elif url == cls.planes_url:
            # Plan Postpago
            products.extend(cls._plans(url, extra_args))
        elif 'catalogo.movistar.cl' in url:
            # Equipo postpago
            products.extend(cls.__celular_postpago(url, extra_args))
        else:
            raise Exception('Invalid URL: ' + url)
        return products

    @classmethod
    def _plans(cls, url, extra_args):
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'python-requests/2.21.0'
        soup = BeautifulSoup(session.get(url, timeout=30).text, 'html5lib')
        products = []

        plan_containers = soup.findAll('div', 'card')

        for plan_container in plan_containers:
            plan_link = plan_container.find('a')
            plan_url = plan_link['href']
            base_plan_name = plan_container.find('h3').text.strip()

            price_text = plan_container.find('div', 'precio').find(
                'span').text
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
    def __celular_postpago(cls, url, extra_args):
        print(url)

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'python-requests/2.21.0'
        session.headers['content-type'] = \
            'application/x-www-form-urlencoded; charset=UTF-8'
        session.headers['x-requested-with'] = 'XMLHttpRequest'
        page = session.get(url)

        if page.url == 'https://catalogo.movistar.cl/tienda/celulares':
            return []
            # raise Exception('Catalogo page URL')

        if page.status_code in [404, 503]:
            # raise Exception('Invalid status code: ' + str(page.status_code))
            return []

        soup = BeautifulSoup(page.text, 'html.parser')
        if soup.find('meta', {'name': 'title'}):
            name = soup.find('meta', {'name': 'title'})['content']
        else:
            raise Exception('No base name found')

        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()
        products = []

        # Prepago
        if cls.include_prepago:
            product_id = soup.find('input', {'id': 'du-product-id'})['value']
            payload = 'id={}'.format(product_id)
            prepago_res = session.post(
                'https://catalogo.movistar.cl/tienda/detalleequipo/'
                'ajax/dataproducto', payload)
            prepago_json = prepago_res.json()
            prepago_price = Decimal(remove_words(prepago_json['special_price']))
            if prepago_price:
                products.append(Product(
                    name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    '{} - Movistar Prepago'.format(sku),
                    -1,
                    prepago_price,
                    prepago_price,
                    'CLP',
                    sku=sku,
                    cell_plan_name='Movistar Prepago',
                    cell_monthly_payment=Decimal(0)
                ))

        # Planes
        for variation in cls.variations:
            regex = "var {} = '(.*)';".format(variation['base_plan'])
            match = re.search(regex, page.text)
            codigo_oferta = match.groups()[0]
            if not codigo_oferta:
                continue
            payload = 'sku={}&codigo_oferta={}'.format(sku, codigo_oferta)

            planes_res = session.post('https://catalogo.movistar.cl/tienda/'
                                      'detalleequipo/ajax/dataplanesproducto',
                                      payload)
            planes = planes_res.json()

            for plan in planes:
                precio_payload = 'sku_plan={}&sku={}&sku_oferta={}'.format(
                    plan['sku_plan'].replace(' ', '+'), sku, codigo_oferta)
                precio_res = session.post(
                    'https://catalogo.movistar.cl/tienda/detalleequipo/'
                    'ajax/datafinanciamientoproducto',
                    precio_payload)
                precio_data = precio_res.json()

                for method_id, plan_name_suffix in variation['methods']:
                    cell_plan_name = plan['name'].strip() + plan_name_suffix
                    if method_id == 1:
                        if 'tarjeta' not in precio_data:
                            continue
                        price = Decimal(remove_words(
                            precio_data['tarjeta']['total']))
                        cell_monthly_payment = Decimal(0)
                    elif method_id == 2:
                        if 'boleta' not in precio_data:
                            continue
                        price = Decimal(remove_words(
                            precio_data['boleta']['pieFormated']))
                        cell_monthly_payment = Decimal(
                            remove_words(precio_data['boleta']['precioCuotas']))
                    elif method_id == 3:
                        if 'mone' not in precio_data:
                            continue
                        price = Decimal(remove_words(
                            precio_data['mone']['pieFormated']))
                        cell_monthly_payment = Decimal(
                            remove_words(precio_data['mone']['precioCuotas']))
                    else:
                        raise Exception('Invalid method ID ', method_id)

                    products.append(Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} - {}'.format(sku, cell_plan_name),
                        -1,
                        price,
                        price,
                        'CLP',
                        sku=sku,
                        cell_plan_name=cell_plan_name,
                        cell_monthly_payment=cell_monthly_payment,
                        allow_zero_prices=True
                    ))

        return products
