import json
from decimal import Decimal

from requests.auth import HTTPBasicAuth

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13


class Tecnoglobal(Store):
    SESSION_COOKIES = None

    categories_dict = {
        'Notebook': ['Computador Notebook']
    }

    @classmethod
    def categories(cls):
        return list(cls.categories_dict.keys())

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        return ['https://www.tecnoglobal.cl/']

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        response = session.get('http://200.6.78.34/stock/v1/price',
                               auth=HTTPBasicAuth(extra_args['username'],
                                                  extra_args['password']))
        sku_entries = json.loads(response.text)['products']
        subcategories = cls.categories_dict[category]

        products = []
        for sku_entry in sku_entries:
            if sku_entry['subCategoria'] not in subcategories:
                continue

            name = sku_entry['descripcion'][:255]
            sku = sku_entry['codigoTg']
            stock = sku_entry['stockDisp']
            price = Decimal(str(sku_entry['precio']))
            currency = sku_entry['tipoMoneda']
            ean = sku_entry['upcEan13']

            if not check_ean13(ean):
                ean = None

            part_number = sku_entry['pnFabricante']

            products.append(Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                price,
                price,
                currency,
                sku=sku,
                ean=ean,
                part_number=part_number
            ))

        return products
