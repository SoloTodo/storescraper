import base64
import time
from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Movistar(Store):
    preferred_discover_urls_concurrency = 1
    prepago_url = 'http://ww2.movistar.cl/prepago/'
    planes_url = 'https://ww2.movistar.cl/movil/planes-portabilidad/'
    cell_catalog_suffix = ''
    requires_movistar_one = False
    variations = [{
            'base_plan': 'EMP_NUM_TAR_5GLibreFullAltasParr',
            'methods': [
                (1, ''),
            ]
        },
        {
            'base_plan': 'EMP_POR_TAR_5GLibreFullPortaParr',
            'methods': [
                (1, ' Portabilidad'),
                (2, ' Portabilidad Cuotas'),
            ]}
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
            time.sleep(5)
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

                catalogo_url = 'https://catalogo.movistar.cl/tienda/' \
                               'celulares?prfilter_ajax=0&prfilter_variables' \
                               '%5Bmodalidades%5D=831&prfilter_ajax=1&p=' \
                               '{}'.format(page)
                print(catalogo_url)
                session = session_with_proxy(extra_args)
                session.headers['user-agent'] = 'python-requests/2.21.0'
                soup = BeautifulSoup(session.get(
                    catalogo_url).json()['productlist'], 'html.parser')
                containers = soup.findAll('li', 'product')

                if not containers:
                    if page == 1:
                        raise Exception('No cells found')
                    break

                for container in containers:
                    product_url = container.find('a')['href'].split('?')[0]
                    print(product_url)

                    product_entries[product_url].append({
                        'category_weight': 1,
                        'section_name': 'Smartphones',
                        'value': idx
                    })

                    if len(container.findAll('div', 'color-label')) > 1:
                        product_soup = BeautifulSoup(
                            session.get(product_url).text, 'html.parser')

                        color_list = product_soup.find(
                            'div', 'container-colores')

                        if color_list:
                            for color_element in color_list.findAll('a')[1:]:
                                sku_url = color_element['href'].split('?')[0]
                                product_entries[sku_url].append({
                                    'category_weight': 1,
                                    'section_name': 'Smartphones',
                                    'value': idx
                                })
                        else:
                            color_list = product_soup.find('ul',
                                                           'colorEMP')

                            if color_list:
                                for color_element in color_list.findAll('a'):
                                    sku_url = color_element[
                                        'data-url-key'].split('?')[0]
                                    product_entries[sku_url].append({
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
    def __celular_postpago(cls, url, extra_args):
        print(url)

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'python-requests/2.21.0'
        page = session.get(url)

        if page.url == 'https://catalogo.movistar.cl/tienda/celulares':
            return []
            # raise Exception('Catalogo page URL')

        if page.status_code in [404, 503]:
            raise Exception('Invalid status code: ' + str(page.status_code))

        soup = BeautifulSoup(page.text, 'html.parser')
        if soup.find('meta', {'name': 'title'}):
            name = soup.find('meta', {'name': 'title'})['content']
        else:
            raise Exception('No base name found')

        sku_status = soup.find('div', 'current-status')

        if not sku_status:
            return []

        if cls.requires_movistar_one and sku_status['data-movistar1'] == 'No':
            return []

        products = []
        base_url = url.split('?')[0]
        raw_sku = soup.select_one(
            'form#product_addtocart_form')['data-product-sku']
        assert raw_sku.endswith('NU')
        base_sku = raw_sku[:-2]

        for variation in cls.variations:
            print(base_sku, variation['base_plan'])
            code = '{}{}'.format(base_sku, variation['base_plan'])
            print(code)
            url = '{}?codigo={}'.format(base_url, base64.b64encode(
                    code.encode('utf-8')).decode('utf-8'))
            print(url)

            res = session.get(url)
            assert res.url == url, res.url
            soup = BeautifulSoup(res.text, 'html.parser')

            for method_id, plan_name_suffix in variation['methods']:
                plan_tags = soup.findAll('div', {'data-method': str(method_id)})

                for plan_tag in plan_tags:
                    cell_plan_name = plan_tag.select_one('p.boxPlanesEmp-plan b').text.split(
                        ':')[0].strip() + plan_name_suffix

                    if method_id == 1:
                        price = Decimal(plan_tag['data-price']).quantize(0)
                        cell_monthly_payment = Decimal(0)
                    elif method_id in [2, 3]:
                        price = Decimal(remove_words(
                            plan_tag.find('p',
                                          'boxEMPlan-int-box-pie').text.split(
                                '$')[1]))
                        cell_monthly_payment = Decimal(remove_words(
                            plan_tag.select_one(
                                'p.boxEMPlan-int-meses b').text))
                    else:
                        raise Exception('Invalid method ID ', method_id)

                    products.append(Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} - {}'.format(base_sku, cell_plan_name),
                        -1,
                        price,
                        price,
                        'CLP',
                        sku=base_sku,
                        cell_plan_name=cell_plan_name,
                        cell_monthly_payment=cell_monthly_payment
                    ))

        return products
