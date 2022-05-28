import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.stores import Paris
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import \
    remove_words, session_with_proxy, CF_REQUEST_HEADERS


class ParisFast(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 10

    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            # 'Camera',
            'StereoSystem',
            # 'OpticalDiskPlayer',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Projector',
            'VideoGameConsole',
            # 'Monitor',
            'AllInOne',
            'AirConditioner',
            # 'WaterHeater',
            # 'SolidStateDrive',
            'SpaceHeater',
            'Wearable',
            'Mouse',
            'Keyboard',
            # 'KeyboardMouseCombo',
            'Headphones',
            # 'ComputerCase',
            'DishWasher',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        return [category]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        from .paris import Paris

        if extra_args and extra_args.get('source', None) == 'keyword_search':
            return Paris.products_for_url(
                url, category, extra_args)

        category_paths = Paris.category_paths

        session = session_with_proxy(extra_args)
        products_dict = {}

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            if category_weight == 0:
                continue

            page = 0

            while True:
                if page > 150:
                    raise Exception('Page overflow:' + category_path)

                category_url = 'https://www.paris.cl/{}/?sz=40&start={}'\
                    .format(category_path, page * 40)
                print(category_url)
                response = session.get(category_url)

                if response.url != category_url:
                    raise Exception('Mismatching URL: {} - {}'.format(
                        response.url, category_url))

                soup = BeautifulSoup(response.text, 'html.parser')
                containers = soup \
                    .find('ul', {'id': 'search-result-items'}) \
                    .findAll('li', recursive=False)

                if not containers:
                    if page == 0:
                        raise Exception('Empty category: ' + category_path)
                    break

                for idx, container in enumerate(containers):
                    product_a = container.find('a')
                    if not product_a:
                        continue
                    product_url = product_a['href'].split('?')[0]
                    if product_url == "null":
                        continue

                    product = cls._get_product(container, category)

                    if not product:
                        continue

                    if product.sku in products_dict:
                        product_to_update = products_dict[product.sku]
                    else:
                        products_dict[product.sku] = product
                        product_to_update = product

                    product_to_update.positions[section_name] = \
                        40 * page + idx + 1

                page += 1

                if page > 30:
                    break

        products_list = [p for p in products_dict.values()]
        return products_list

    @classmethod
    def _get_product(cls, container, category):
        product_url = container.find('a')['href'].split('?')[0]
        if 'https' not in product_url:
            product_url = 'https://www.paris.cl' + product_url

        product_tile = container.find('div', 'product-tile')

        if 'data-product' not in product_tile.attrs:
            return None

        data = json.loads(product_tile['data-product'])
        name = data['name']
        sku = data['variant']

        seller_info = data.get('dimension3', None)
        if seller_info == 'MARKETPLACE':
            seller = 'MARKETPLACE'
        else:
            seller = None

        normal_price = Decimal(data['price'])
        if data['dimension20']:
            offer_price = Decimal(data['dimension20'])
        else:
            offer_price = normal_price

        stock = -1

        p = Product(
            name,
            cls.__name__,
            category,
            product_url,
            product_url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            seller=seller
        )

        return p

    @classmethod
    def banners(cls, extra_args=None):
        from .paris import Paris
        return Paris.banners(extra_args=extra_args)

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        from .paris import Paris
        return Paris.discover_urls_for_keyword(
            keyword=keyword, threshold=threshold, extra_args=extra_args)
