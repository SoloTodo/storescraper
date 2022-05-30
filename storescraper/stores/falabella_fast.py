import json
import logging
from decimal import Decimal

from storescraper.stores import Falabella
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import \
    remove_words, session_with_proxy, CF_REQUEST_HEADERS


class FalabellaFast(Store):
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
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Projector',
            'VideoGameConsole',
            # 'CellAccesory',
            'AllInOne',
            'AirConditioner',
            'Monitor',
            'WaterHeater',
            # 'SolidStateDrive',
            'Mouse',
            'SpaceHeater',
            'Keyboard',
            # 'KeyboardMouseCombo',
            'Wearable',
            'Headphones',
            'DishWasher'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        return [category]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        from .falabella import Falabella

        if extra_args and extra_args.get('source', None) == 'keyword_search':
            return Falabella.products_for_url(
                url, category, extra_args)

        category_paths = Falabella.category_paths

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = CF_REQUEST_HEADERS['User-Agent']
        products_dict = {}

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = \
                e[:4]

            if len(e) > 4:
                extra_query_params = e[4]
            else:
                extra_query_params = None

            if category not in local_categories:
                continue

            products_data = cls._get_products_data(
                session, category_id, extra_query_params)

            for idx, product_data in enumerate(products_data):
                products = cls._get_products(product_data, category)

                for product in products:
                    if product.sku in products_dict:
                        product_to_update = products_dict[product.sku]
                    else:
                        products_dict[product.sku] = product
                        product_to_update = product

                    product_to_update.positions[section_name] = idx + 1

        products_list = [p for p in products_dict.values()]
        return products_list

    @classmethod
    def _get_products_data(cls, session, category_id, extra_query_params):
        products_data = []
        base_url = 'https://www.falabella.com/s/browse/v1/listing/cl?' \
                   'zones=ZL_CERRILLOS%2CLOSC%2C130617%2C13' \
                   '&categoryId={}&page={}'

        page = 1

        while True:
            if page > 200:
                raise Exception('Page overflow: ' + category_id)

            pag_url = base_url.format(category_id, page)
            print(pag_url)

            if extra_query_params:
                pag_url += '&' + extra_query_params

            res = Falabella.retrieve_json_page(session, pag_url)

            if 'results' not in res or not res['results']:
                if page == 1:
                    logging.warning('Empty category: {}'.format(category_id))
                break

            for result in res['results']:
                products_data.append(result)

            page += 1

            if page > 50:
                break

        return products_data

    @classmethod
    def _get_products(cls, product_data, category):
        products = []

        product_url = product_data['url']
        product_name = product_data['displayName']
        product_sku = product_data['skuId']
        product_stock = -1

        prices = product_data['prices']
        offer_price = None
        normal_price = None

        for price in prices:
            if price['label'] == '(Oferta)' or price['type'] == 'eventPrice':
                normal_price = Decimal(remove_words(price['price'][0]))
                break
            if price['icons'] == 'cmr-icon':
                continue
            normal_price = Decimal(remove_words(price['price'][0]))

        for price in prices:
            if price['icons'] == 'cmr-icon':
                offer_price = Decimal(remove_words(price['price'][0]))

        if not normal_price:
            normal_price = offer_price

        if not offer_price:
            offer_price = normal_price

        variants = product_data['variants'][0]['options']

        if variants:
            for variant in variants:
                variant_sku = variant['extraInfo']
                variant_name = '{} ({})'.format(product_name, variant['label'])
                p = Product(
                    variant_name,
                    cls.__name__,
                    category,
                    product_url,
                    product_url,
                    variant_sku,
                    product_stock,
                    normal_price,
                    offer_price,
                    'CLP',
                    sku=variant_sku
                )
                products.append(p)

        else:
            p = Product(
                product_name,
                cls.__name__,
                category,
                product_url,
                product_url,
                product_sku,
                product_stock,
                normal_price,
                offer_price,
                'CLP',
                sku=product_sku,
            )
            products.append(p)

        return products

    @classmethod
    def banners(cls, extra_args=None):
        from .falabella import Falabella
        return Falabella.banners(extra_args=extra_args)

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        from .falabella import Falabella
        return Falabella.discover_urls_for_keyword(
            keyword=keyword, threshold=threshold, extra_args=extra_args)
