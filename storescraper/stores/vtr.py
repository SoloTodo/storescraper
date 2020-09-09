import json
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


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
                'https://www.vtr.com/ccstoreui/v1/search?'
                'Ntk=product.category&Ntt=Equipments&No=0&'
                'Nrpp=100&Ns=Device.x_OrderForCollectionPage%7C0').text)

            if not data:
                raise Exception('Empty cell category')

            for record in data['resultsList']['records']:
                product_id = record['attributes']['product.repositoryId'][0]
                product_url = 'https://www.vtr.com/product/{}'.format(
                    product_id)
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
            'https://www.vtr.com/ccstoreui/v1/products?categoryId='
            'MovilesPlanes&fields=items.displayName%2C'
            'items.childSKUs.x_relatedDeviceProductId%2C'
            'items.childSKUs.listPrice').text)
        cuotas_suffixes = [
            (' Portabilidad (con cuota de arriendo)', Decimal('1.0')),
            (' Portabilidad (sin cuota de arriendo)', Decimal('0.7')),
            ('', Decimal('0.9'))
        ]
        products = []

        for plan_entry in json_data['items']:
            base_plan_name = plan_entry['displayName']

            base_price = None
            for child_sku in plan_entry['childSKUs']:
                if not child_sku['x_relatedDeviceProductId']:
                    base_price = Decimal(child_sku['listPrice'])
                    break

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
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        prod_id = url.split('?')[0].split('/')[-1]

        page_metadata = json.loads(
            soup.find('script', {'id': 'CC-schema-org-server'}).text)
        cell_base_name = page_metadata['name']
        base_price = Decimal('Inf')
        variants = []

        for entry in page_metadata['offers']:
            variants.append(entry['itemOffered']['productID'])
            variant_price = Decimal(entry['price'])
            # for some reason VTR only displays the lowest variant price,
            # so use the same behavior
            if variant_price < base_price:
                base_price = variant_price

        product_json_url = 'https://www.vtr.com/ccstoreui/v1/pages/product/' \
                          '{}'.format(prod_id)
        product_json = json.loads(session.get(product_json_url).text)
        product_with_plan_ids = product_json[
            'data']['page']['product']['x_BundlePlanSkusIds']
        print(product_with_plan_ids)

        product_plan_pricing_url = \
            'https://www.vtr.com/ccstoreui/v1/skus?skuIds={}&fields=active' \
            '%2ClistPrice%2CparentProducts.displayName%2CdisplayName%2Cx' \
            '_priceDiscountForPortability%2Cx_priceDiscountForPortability' \
            ''.format(urllib.parse.quote(product_with_plan_ids))
        pricing_entries = json.loads(
            session.get(product_plan_pricing_url).text)

        variant_data = [
            (' Portabilidad Cuotas', True),
            (' Portabilidad', False),
            ('', False)
        ]

        products = []

        for variant in variants:  # [S20_Black, S20_Silver]
            cell_name = '{} ({})'.format(cell_base_name, variant)

            for pricing_entry in pricing_entries['items']:  # Each plan
                base_plan_name = pricing_entry['parentProducts'][
                    0]['displayName']
                portability_cuotas_price = Decimal(
                    pricing_entry['listPrice'] -
                    pricing_entry['x_priceDiscountForPortability']
                )
                for name_suffix, use_portability_cuotas_price in variant_data:
                    cell_plan_name = 'VTR ' + base_plan_name + name_suffix
                    if use_portability_cuotas_price:
                        price = portability_cuotas_price
                    else:
                        price = base_price

                    p = Product(
                        cell_name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} {} {}'.format(prod_id, variant, cell_plan_name),
                        -1,
                        price,
                        price,
                        'CLP',
                        sku=prod_id,
                        cell_plan_name=cell_plan_name,
                        picture_urls=None,
                        cell_monthly_payment=Decimal(0)
                    )
                    products.append(p)
        return products
