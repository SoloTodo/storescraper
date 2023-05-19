import base64
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

                catalogo_url = 'https://catalogo.movistar.cl/tienda/' \
                               'celulares/equipos-con-plan?p={}'.format(
                                page) + cls.cell_catalog_suffix
                print(catalogo_url)
                session = session_with_proxy(extra_args)
                session.headers['user-agent'] = 'python-requests/2.21.0'
                soup = BeautifulSoup(session.get(
                    catalogo_url).text, 'html.parser')
                containers = soup.findAll('li', 'product')

                if not containers:
                    if page == 1:
                        raise Exception('No cells found')
                    break

                for container in containers:
                    product_url = container.find('a')['href'].split('?')[0]
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

        color_list = soup.find('ul', 'colorEMP')
        if not color_list:
            return []

        for color_container in color_list.findAll('li'):
            color_element = color_container.find('a')
            sku_url = color_element['data-url-key']
            products.extend(cls.__celular_postpago(sku_url, extra_args))

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
        if sku_status['data-type'] != '1':
            return []

        products = []
        base_url = url.split('?')[0]
        raw_sku = soup.select_one(
            'form#product_addtocart_form')['data-product-sku']
        assert raw_sku.endswith('NU')
        base_sku = raw_sku[:-2]

        # Planes asociados
        plans = []
        plan_cells = soup.find('div', 'planesHtml').findAll('article')
        for plan_cell in plan_cells:
            plan_name = plan_cell['data-name'].strip()
            plans.append(plan_name)

        # Número nuevo
        code = '{}EMP_NUM_TAR_5GLibreFullAltasParr'.format(base_sku)
        url = '{}?codigo={}'.format(base_url, base64.b64encode(
                code.encode('utf-8')).decode('utf-8'))
        print(url)

        res = session.get(url)
        assert res.url == url, res.url
        soup = BeautifulSoup(res.text, 'html.parser')
        price_tag = soup.find('div', {'data-method': '1'})
        price = Decimal(price_tag['data-price']).quantize(0)

        for plan in plans:
            products.append(Product(
                name,
                cls.__name__,
                'Cell',
                url,
                url,
                '{} - {}'.format(base_sku, plan),
                -1,
                price,
                price,
                'CLP',
                sku=base_sku,
                cell_plan_name=plan,
                cell_monthly_payment=Decimal(0)
            ))

        # Portabilidad
        code = '{}EMP_POR_TAR_5GLibreFullPortaParr'.format(base_sku)
        url = '{}?codigo={}'.format(base_url, base64.b64encode(
            code.encode('utf-8')).decode('utf-8'))
        print(url)

        res = session.get(url)
        assert res.url == url, res.url
        soup = BeautifulSoup(res.text, 'html.parser')

        # Con arriendo
        price_tag = soup.find('p', 'boxEMPlan-int-meses').parent
        price = Decimal(remove_words(price_tag.find(
            'p', 'boxEMPlan-int-box-pie').contents[1]))
        cell_monthly_payment = Decimal(remove_words(
            price_tag.find('p',
                           'boxEMPlan-int-meses').find('b').text))

        for plan in plans:
            final_plan_name = '{} Portabilidad Cuotas'.format(plan)
            products.append(Product(
                name,
                cls.__name__,
                'Cell',
                url,
                url,
                '{} - {}'.format(base_sku, final_plan_name),
                -1,
                price,
                price,
                'CLP',
                sku=base_sku,
                cell_plan_name=final_plan_name,
                cell_monthly_payment=cell_monthly_payment
            ))

        # Sin arriendo
        price_tag = soup.find('div', {'data-method': '1'})
        price = Decimal(price_tag['data-price']).quantize(0)

        for plan in plans:
            final_plan_name = '{} Portabilidad'.format(plan)
            products.append(Product(
                name,
                cls.__name__,
                'Cell',
                url,
                url,
                '{} - {}'.format(base_sku, final_plan_name),
                -1,
                price,
                price,
                'CLP',
                sku=base_sku,
                cell_plan_name=final_plan_name,
                cell_monthly_payment=Decimal(0)
            ))

        return products
