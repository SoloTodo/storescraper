from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import TELEVISION


class Sukasa(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        endpoint = ('https://api.comohogar.com/catalog-api/products-es/all?'
                    'pageSize=1000&active=true&brandId=60966430-ee8d-11ed-b56d-005056010420')
        product_urls = []

        response = session.get(endpoint)
        products_data = response.json()['entities']

        if not products_data:
            raise Exception('Empty store')

        for product in products_data[0]['products']:
            product_url = 'https://www.sukasa.com/productos/{}?id={}'.format(product['slug'], product['id'])
            if product_url not in product_urls:
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        product_id = url.split('?id=')[1]
        session = session_with_proxy(extra_args)
        endpoint = 'https://api.comohogar.com//catalog-api/products/portal/{}'.format(product_id)
        response = session.get(endpoint)
        product_data = response.json()
        name = product_data['name']
        sku = product_data['cmInternalCode']
        price = Decimal(str(product_data['cmItmPvpAfIva']))
        stock = product_data['cmStock']
        for store in product_data['storeList']:
            stock += store['quantity']
        picture_urls = [res['resourceUrl'] for res in product_data['resources']]
        description = html_to_markdown(product_data['longDescription'])
        part_number = product_data['cmModel']

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number
        )

        return [p]
