import json

from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Lucila(Store):
    url = 'http://www.kitthss.cl/lucila-go.html'

    @classmethod
    def categories(cls):
        return [
            'Lamp',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['10761660042', 'Lamp'],
            ['10520719114', 'Lamp'],
            ['10511054730', 'Lamp'],
            ['10520625354', 'Lamp'],
            ['10510992074', 'Lamp'],
            ['10761698698', 'Lamp'],
        ]

        discovered_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            discovery_url = 'https://lucila-filamentos-led.myshopify.com/' \
                            'api/apps/6/product_listings/' + category_path

            discovered_urls.append(discovery_url)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['Authorization'] = 'Basic OGRiZDViZGY4M2Y5NzA3MTlkY' \
                                           'jE2NmRiODdhZDZhNWQ='
        data = json.loads(session.get(url).text)

        products = []

        for product_entry in data['product_listing']['variants']:
            if product_entry['available']:
                stock = -1
            else:
                stock = 0

            name = product_entry['title'].strip()
            sku = str(product_entry['id'])
            price = Decimal(product_entry['price'])
            product_url = cls.url

            p = Product(
                name,
                cls.__name__,
                category,
                product_url,
                url,
                sku,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
            )
            products.append(p)

        return products
