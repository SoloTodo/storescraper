import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Vtr(Store):
    prepago_url = 'https://vtr.com/productos/moviles/prepago'
    planes_url = 'https://vtr.com/productos/moviles/product.clasificacion/' \
                 'MovilesPlanes/'

    @classmethod
    def categories(cls):
        return [
            'CellPlan',
            'Cell'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []

        if category == 'CellPlan':
            product_urls.extend([
                cls.prepago_url,
                cls.planes_url
            ])
        elif category == 'Cell':
            session = session_with_proxy(extra_args)
            soup = BeautifulSoup(
                session.get('https://vtr.com/productos/moviles/'
                            'product.clasificacion/MovilesEquipos').text,
                'html.parser')

            containers = soup.findAll('div', 'mep-device-module')

            if not containers:
                raise Exception('Empty cell category')

            for container in containers:
                product_path = container.find('a')['href'].split('?')[0]
                product_url = 'https://vtr.com' + product_path
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = []
        if url == cls.prepago_url:
            # Plan Prepago
            p = Product(
                'VTR Prepago',
                cls.__name__,
                category,
                url,
                url,
                'VTR Prepago',
                -1,
                Decimal(0),
                Decimal(0),
                'CLP',
            )
            products.append(p)
        elif url == cls.planes_url:
            # Plan Postpago
            products.extend(cls._plans(url, extra_args))
        elif 'productos/detalle' in url:
            # Equipo postpago
            products.extend(cls._celular_postpago(url, extra_args))
        else:
            raise Exception('Invalid URL: ' + url)
        return products

    @classmethod
    def _plans(cls, url, extra_args):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        products = []

        rows = soup.findAll('div', 'box-vertical-fijo')

        portability_suffixes = [
            ('', 'data-not-ported'),
            (' Portabilidad', 'data-ported')
        ]
        cuotas_suffixes = [
            ' (sin cuota de arriendo)',
            ' (con cuota de arriendo)'
        ]

        for row in rows:
            base_plan_name = ' '.join(
                [x.replace('\n', '').strip()
                 for x in row.find('li', 'gbs_text').text.split()]
            )
            price_container = row.find('div', 'price')

            for portability_suffix, price_field in portability_suffixes:
                price = Decimal(remove_words(
                    price_container[price_field]))

                for cuota_suffix in cuotas_suffixes:
                    plan_name = '{}{}{}'.format(
                        base_plan_name, portability_suffix, cuota_suffix)

                    p = Product(
                        plan_name,
                        cls.__name__,
                        'CellPlan',
                        url,
                        url,
                        plan_name,
                        -1,
                        price,
                        price,
                        'CLP',
                    )

                    products.append(p)

        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h3', 'mep-model').text.strip()
        sku = re.search(r'prod(\d+)', url).groups()[0]

        picture_urls = ['https://vtr.com' + tag['src'].strip().replace(
            ' ', '%20') for tag in soup.findAll('img', 'color-0')]

        description = html_to_markdown(
            str(soup.find('div', 'vtr-cont-planes')), 'https://vtr.com')

        colors = []

        for tag in soup.find('ul', 'devices-colors').findAll('li'):
            if tag.find('div', 'saleOut'):
                continue

            colors.append(tag['color-name'])

        plan_buttons = soup.findAll('button', 'c2cbtn')

        products = []

        for color in colors:
            name_with_color = '{} - {}'.format(name, color)
            cell_url = '{}?selection={}'.format(url, color)

            for plan_button in plan_buttons:
                # Sanity checks
                assert plan_button['planpriceport'] == \
                       plan_button['planpricenoport'] == \
                       plan_button['planoriginprice']
                assert plan_button['deviceprice'] == \
                    plan_button['pixel-price'] == \
                    plan_button['om-price'] == \
                    plan_button['pieinicialprice']

                parent_row = plan_button.findParent('tr')
                if not parent_row:
                    parent_row = plan_button.findParent()
                parent_row_style = parent_row.get('style', '')

                if 'display' in parent_row_style:
                    continue

                portability_name = plan_button['port']

                if portability_name == 'Portados':
                    name_suffix = ' Portabilidad'
                    cell_monthly_payment_factor = Decimal('0.3')
                elif portability_name == 'No Portados':
                    name_suffix = ''
                    cell_monthly_payment_factor = Decimal('0.1')
                else:
                    raise Exception('Invalid portability choice')

                plan_name = 'VTR {}{}'.format(
                    plan_button['planname'].strip(), name_suffix)

                # Sin cuota de arriendo

                price = Decimal(plan_button['devicefullprice']).quantize(0)

                p = Product(
                    name_with_color,
                    cls.__name__,
                    'Cell',
                    cell_url,
                    url,
                    '{} {} {}'.format(sku, color, plan_name),
                    -1,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    cell_plan_name=plan_name,
                    picture_urls=picture_urls,
                    description=description,
                    cell_monthly_payment=Decimal(0)
                )
                products.append(p)

                # Con cuota de arriendo

                price = Decimal(plan_button['deviceprice']).quantize(0)
                plan_base_price = Decimal(plan_button['planpriceport'])
                cell_monthly_payment = \
                    plan_base_price * cell_monthly_payment_factor

                p = Product(
                    name_with_color,
                    cls.__name__,
                    'Cell',
                    cell_url,
                    url,
                    '{} {} {} Cuotas'.format(sku, color, plan_name),
                    -1,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    cell_plan_name=plan_name + ' Cuotas',
                    picture_urls=picture_urls,
                    description=description,
                    cell_monthly_payment=cell_monthly_payment
                )
                products.append(p)

        return products
