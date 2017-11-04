import json

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
                 'MovilesPlanes'

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

            containers = soup.findAll('div', 'vtr-box-shadow')

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

        plan_types = [
            ('cont-no-portar', ''),
            # ('cont-si-portar', 'Portabilidad Sin Equipo'),
        ]

        for panel_class, suffix in plan_types:
            for panel in soup.findAll('div', panel_class):
                for plan_table in panel.findAll('tbody')[::2]:
                    plan_row = plan_table.find('tr')
                    cells = plan_row.findAll('td')

                    name = cells[0].contents[0].strip()
                    price = Decimal(remove_words(cells[1].text))

                    p = Product(
                        name,
                        cls.__name__,
                        'CellPlan',
                        url,
                        url,
                        name,
                        -1,
                        price,
                        price,
                        'CLP',
                    )

                    products.append(p)

                    portablidad_name = '{} Portabilidad'.format(name)

                    p = Product(
                        portablidad_name,
                        cls.__name__,
                        'CellPlan',
                        url,
                        url,
                        portablidad_name,
                        -1,
                        price,
                        price,
                        'CLP',
                    )

                    products.append(p)

        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h2', {'id': 'nombre-equipo'}).text.strip()
        sku = re.search(r'prod(\d+)', url).groups()[0]

        picture_urls = ['https://vtr.com' + tag['src'] for tag in
                        soup.findAll('img', 'color-0')]

        description = ''

        for panel_id in ['manuales_equipo', 'especificaciones-equipo']:
            panel = soup.find('div', {'id': panel_id})
            description += html_to_markdown(str(panel)) + '\n\n'

        description += html_to_markdown(str(soup.find('div', 'bg-grey-light')))

        plan_types = [
            ('cont-no-portar', ''),
            ('cont-si-portar', ' Portabilidad'),
        ]

        products = []

        for panel_class, suffix in plan_types:
            for panel in soup.findAll('div', panel_class):
                for plan_table in panel.findAll('tbody'):
                    row = plan_table.find('tr', 'mobile-accordion-button')
                    if not row:
                        continue

                    cells = row.findAll('td')

                    price = Decimal(remove_words(row.find('span').text))

                    plan_name = cells[1].contents[0].strip() + suffix

                    p = Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} {}'.format(sku, plan_name),
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

        return products
