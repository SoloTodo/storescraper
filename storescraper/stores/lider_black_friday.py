import json

from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class LiderBlackFriday(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'VideoGameConsole',
            'AllInOne',
            'Projector',
            'SpaceHeater',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        return ['https://blackfriday.lider.cl/?cat={}'.format(category)]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        categories_dict = {
            'Notebook': 'Computación',
            'Cell': 'Smartphones',
            # 'Refrigerator': 'Refrigeración',
            'Refrigerator': 'Línea Blanca',
            'Oven': 'Electrodomésticos',
            'Television': 'Televisión',
            'StereoSystem': 'Audio',
            'Printer': 'Impresoras',
            'VideoGameConsole': 'Consolas'
        }

        if category and category not in categories_dict:
            return []

        session = session_with_proxy(extra_args)

        product_to_stock = {}
        stocks = json.loads(session.get('https://blackfriday.lider.cl/'
                                        'json/ff_inv_landing.json').text)

        for stocks in stocks['Inventory']:
            for sku, sku_stock_info in stocks.items():
                product_to_stock[sku] = sku_stock_info['stock']

        json_products = json.loads(
            session.get(
                'https://blackfriday.lider.cl/json/products.json').text)[
            'products']

        products = []
        category_keyword = categories_dict[category] if category else None

        for json_product in json_products:
            if category_keyword and category_keyword not in \
                    json_product['categorias']:
                continue

            product_url = 'https://blackfriday.lider.cl/#!/product/' \
                          + json_product['ID']

            brand = json_product['brand']
            model = json_product['displayName']
            name = '{} {}'.format(brand, model)
            sku = json_product['sku']

            print(sku)

            if isinstance(json_product['price'], list):
                print(json_product)
                continue

            normal_price = Decimal(json_product['price']['BasePriceSales'])
            offer_price = Decimal(
                json_product['price']['BasePriceTLMC'] or '0')

            if not offer_price:
                offer_price = normal_price

            stock = product_to_stock.get('PROD_' + sku, None)

            if stock is None:
                stock = 0
            elif stock < 0:
                stock = 0

            p = Product(
                name,
                cls.__name__,
                category,
                product_url,
                url,
                sku,
                stock,
                normal_price,
                offer_price,
                'CLP',
                sku=sku
            )

            products.append(p)

        return products
