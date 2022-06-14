import json
import logging
from bs4 import BeautifulSoup
from decimal import Decimal
from storescraper.categories import AIR_CONDITIONER, CELL, OVEN, \
    REFRIGERATOR, STEREO_SYSTEM, STOVE, TELEVISION, WASHING_MACHINE

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Olier(Store):
    base_url = 'https://www.lg.com'
    country_code = 'cl'

    @classmethod
    def categories(cls):
        return [
            OVEN,
            TELEVISION,
            STEREO_SYSTEM,
            CELL,
            REFRIGERATOR,
            STOVE,
            WASHING_MACHINE,
            AIR_CONDITIONER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        return [category]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        category_paths = [
            ['163', STOVE],
            ['169', OVEN],
            ['173', OVEN],
            ['171', WASHING_MACHINE],
            ['192', WASHING_MACHINE],
            ['175', WASHING_MACHINE],
            ['197', STEREO_SYSTEM],
            ['98', TELEVISION],
            ['97', STEREO_SYSTEM],
            ['99', STEREO_SYSTEM],
            ['187', CELL],
            ['148', REFRIGERATOR],
            ['146', REFRIGERATOR],
            ['193', STOVE],
            ['91', AIR_CONDITIONER],
        ]

        session = session_with_proxy(extra_args)
        products = []
        base_url = 'https://www.olier.com.py/get-productos' \
            '?page={}&categoria={}'

        for c in category_paths:
            category_path, local_category = c

            if category != local_category:
                continue

            page = 1

            while True:
                url = base_url.format(page, category_path)

                if page >= 15:
                    raise Exception('Page overflow: ' + url)

                print(url)

                data = session.get(url).text
                product_containers = json.loads(data)['paginacion']['data']

                if len(product_containers) == 0:
                    if page == 1:
                        logging.warning('Empty category: ' + category_path)
                    break

                for product in product_containers:
                    name = product['nombre']
                    sku = product['codigo_articulo']
                    ean = product.get('ean', None)
                    url_ver = product['url_ver']
                    price = Decimal(product['precio_retail'])
                    stock = product['existencia']
                    picture_urls = []
                    for i in product['imagenes']:
                        if i['url_imagen']:
                            picture_urls.append(
                                'https://www.olier.com.py/storage/sku/' +
                                i['url_imagen'])

                    p = Product(
                        name,
                        cls.__name__,
                        category,
                        url_ver,
                        url_ver,
                        sku,
                        stock,
                        price,
                        price,
                        'PYG',
                        sku=sku,
                        ean=ean,
                        picture_urls=picture_urls
                    )
                    products.append(p)

                page += 1

        return products
