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

            containers = soup.findAll('div', 'select-device-box')

            if not containers:
                raise Exception('Empty cell category')

            for container in containers:
                product_path = container.find('a')['href'].split('#')[0]
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

        plan_containers = [
            ('Libre', 'planes-multimedia'),
            ('Cuenta Controlada', 'planes-multimedia-cuenta-controlada'),
            ('Plus', 'planes-plus')
        ]

        for plan_family, container_id in plan_containers:
            container = soup.find('li', {'id': container_id})
            rows = container.findAll('div', 'mobile-plan-box')[1:]

            for row in rows:
                name = '{} {}'.format(
                    plan_family, row.find('span', 'colored').text.strip())
                price_container = row.find(
                    'div', 'not-device').find('span', 'price')

                price = Decimal(remove_words(
                    price_container['data-not-ported']))

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
                price = Decimal(remove_words(price_container['data-ported']))

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
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h2').find('strong').text.strip()
        sku = re.search(r'prod(\d+)', url).groups()[0]

        picture_urls = ['https://vtr.com' + tag['src'] for tag in
                        soup.findAll('img', 'color-0')]

        description = ''

        for panel in soup.findAll('div', 'tab_content'):
            description += html_to_markdown(
                str(panel), 'https://vtr.com') + '\n\n'

        plan_families = [
            ('Libre', 'planes-multimedia'),
            ('Cuenta Controlada', 'planes-multimedia-cuenta-controlada'),
            ('Plus', 'planes-plus')
        ]

        plan_types = [
            ('cont-no-portar', ''),
            ('cont-si-portar', ' Portabilidad'),
        ]

        colors = [tag.parent.text.strip()
                  for tag in soup.findAll('span', 'square')]

        products = []

        for color in colors:
            name_with_color = '{} - {}'.format(name, color)

            for plan_type, panel_id in plan_families:
                panel = soup.find('li', {'id': panel_id})

                for panel_class, suffix in plan_types:
                    card = panel.find('div', panel_class)

                    for row in card.findAll('div', 'mobile-plan-box'):
                        price_container = row.find('span', 'price')

                        if len(price_container.contents) == 3:
                            price_text = price_container.text
                        else:
                            price_text = price_container.contents[2]

                        price = Decimal(remove_words(price_text))

                        plan_name = '{} {}{}'.format(
                            plan_type,
                            row.findAll('span', 'units')[1].text.strip(),
                            suffix)

                        p = Product(
                            name_with_color,
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
