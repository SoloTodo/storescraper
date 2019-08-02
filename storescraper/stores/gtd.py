import json
import re

from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Gtd(Store):
    prepago_url = 'https://nuevo.gtdmanquehue.com/telefonia-movil'
    equipos_url = 'https://nuevo.gtdmanquehue.com/negocios/' \
                  'telefonia-movil/equipos'

    @classmethod
    def categories(cls):
        return [
            'Cell',
            'CellPlan'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []

        if category == 'CellPlan':
            product_urls.append(cls.prepago_url)

        if category == 'Cell':
            product_urls.append(cls.equipos_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = []
        if url == cls.prepago_url:
            # Plan Prepago
            p = Product(
                'GTD Prepago',
                cls.__name__,
                category,
                url,
                url,
                'Claro Prepago',
                -1,
                Decimal(0),
                Decimal(0),
                'CLP',
            )
            products.append(p)
        elif url == cls.equipos_url:
            session = session_with_proxy(extra_args)
            body = session.get(url).text
            json_body = re.search(r'var catalog = (.+)', body).groups()[0][:-1]
            json_body = json.loads(json_body)

            for json_product in json_body['products']:
                if not json_product['published']:
                    continue

                name = json_product['name']
                sku = json_product['id']
                price = Decimal(remove_words(json_product['leasing_price']))
                description = html_to_markdown(json_product['description'])

                picture_urls = [
                    'https://nuevo.gtdmanquehue.com' + im['options']['url']
                    for im in json_product['images']
                ]

                product = Product(
                    name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    sku,
                    -1,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    cell_plan_name='GTD Prepago',
                    description=description,
                    picture_urls=picture_urls
                )

                products.append(product)
        else:
            raise Exception('Invalid URL: ' + url)

        return products
