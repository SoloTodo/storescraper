import json
from urllib.parse import urlparse, parse_qs

from decimal import Decimal

from storescraper.categories import CELL
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Vtr(Store):
    prepago_url = 'https://vtr.com/productos/moviles/prepago'
    planes_url = 'https://www.vtr.com/moviles/MovilesPlanes-planes-multimedia'

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

            data = json.loads(session.get(
                'https://vtr.com/api/product/devices').text)

            if not data:
                raise Exception('Empty cell category')

            for record in data:
                in_stock = False
                for variant in record['variantMatrix']:
                    if variant['stockLevelStatus'] == 'inStock':
                        in_stock = True
                        break

                if not in_stock:
                    continue

                product_id = record['code']
                product_url = 'https://vtr.com/productos/details?code={}'\
                    .format(product_id)
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
        elif 'product' in url:
            # Equipo postpago
            products.extend(cls._celular_postpago(url, extra_args))
        else:
            raise Exception('Invalid URL: ' + url)
        return products

    @classmethod
    def _plans(cls, url, extra_args):
        session = session_with_proxy(extra_args)

        json_data = json.loads(session.get(
            'https://vtr.com/cms/product/catalog?category=plans').text)
        cuotas_suffixes = [
            (' Portabilidad (con cuota de arriendo)', Decimal('1.0')),
            (' Portabilidad (sin cuota de arriendo)', Decimal('0.7')),
            ('', Decimal('0.9'))
        ]
        products = []

        for plan_entry in json_data:
            base_plan_name = plan_entry['product_name']

            base_price = None
            for price_entry in plan_entry['price']:
                if price_entry['plan_type'] == 'portability':
                    base_price = (Decimal(remove_words(price_entry['price'])) /
                                  Decimal('0.7')).quantize(0)

            assert base_price

            for suffix, multiplier in cuotas_suffixes:
                price = (base_price * multiplier).quantize(0)
                name = base_plan_name + suffix

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

        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        print(url)
        session = session_with_proxy(extra_args)

        parsed_url = urlparse(url)
        parsed_qs = parse_qs(parsed_url.query)
        prod_id = parsed_qs['code'][0]

        product_data = json.loads(session.get(
            'https://vtr.com/api/product/device?device={}'.format(
                prod_id)).text)

        for plan_entry in product_data['plans']:
            plan_entry['pricing_data'] = {x['name']: x
                                          for x in plan_entry['price']}

        products = []

        for variant in product_data['variantMatrix']:
            stock = -1 if variant['stockLevelStatus'] == 'inStock' else 0
            name = '{} {} ({})'.format(product_data['manufacturer'],
                                       variant['name'], variant['code'])
            picture_urls = [x['url'] for x in variant['images']]

            for plan in product_data['plans']:
                base_cell_plan_name = plan['name'].split(' - ')[0][:40]

                # Sin portabilidad, sin arriendo
                price = Decimal(plan['pricing_data']['COMPRA']['value'])
                products.append(Product(
                    name,
                    cls.__name__,
                    CELL,
                    url,
                    url,
                    '{} - {}'.format(name, base_cell_plan_name),
                    stock,
                    price,
                    price,
                    'CLP',
                    cell_plan_name=base_cell_plan_name,
                    cell_monthly_payment=Decimal(0),
                    picture_urls=picture_urls
                ))

                # Portabilidad sin arriendo
                cell_plan_name = '{} Portabilidad'.format(base_cell_plan_name)
                products.append(Product(
                    name,
                    cls.__name__,
                    CELL,
                    url,
                    url,
                    '{} - {}'.format(name, cell_plan_name),
                    stock,
                    price,
                    price,
                    'CLP',
                    cell_plan_name=cell_plan_name,
                    cell_monthly_payment=Decimal(0),
                    picture_urls=picture_urls
                ))

                # Portabilidad con arriendo
                cell_plan_name = '{} Portabilidad Cuotas'.format(
                    base_cell_plan_name)
                price = Decimal(plan['pricing_data']['ARRIENDO']['value'])
                products.append(Product(
                    name,
                    cls.__name__,
                    CELL,
                    url,
                    url,
                    '{} - {}'.format(name, cell_plan_name),
                    stock,
                    price,
                    price,
                    'CLP',
                    cell_plan_name=cell_plan_name,
                    cell_monthly_payment=Decimal(0),
                    picture_urls=picture_urls
                ))

        return products
