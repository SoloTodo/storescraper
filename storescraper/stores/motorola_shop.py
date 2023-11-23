import base64
import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, vtex_preflight


class MotorolaShop(StoreWithUrlExtensions):
    url_extensions = [
        ('smartphones', CELL)
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        product_urls = []
        session = session_with_proxy(extra_args)

        offset = 0
        while True:
            if offset >= 600:
                raise Exception('Page overflow')

            variables = {
                "from": offset,
                "to": offset + 24,
                "selectedFacets": [{"key": "c", "value": url_extension}]
            }

            payload = {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": extra_args['sha256Hash']
                },
                "variables": base64.b64encode(json.dumps(
                    variables).encode('utf-8')).decode('utf-8')
            }

            endpoint = 'https://www.motorola.cl/_v/segment/graphql/v1' \
                       '?extensions={}'.format(json.dumps(payload))
            response = session.get(endpoint).json()

            product_entries = response['data']['productSearch']['products']

            if not product_entries:
                break

            for product_entry in product_entries:
                product_url = 'https://www.motorola.cl/{}/p'.format(
                    product_entry['linkText'])
                product_urls.append(product_url)

            offset += 24

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')

        product_data_tag = soup.find('template', {'data-varname': '__STATE__'})
        json_product = json.loads(str(
            product_data_tag.find('script').contents[0]))
        item_key = list(json_product.keys())[0]
        products = []
        index = 0
        while True:
            variation_key = '{}.items.{}'.format(item_key, index)
            product = json_product.get(variation_key, None)
            if not product:
                break

            product = json_product[variation_key]
            name = product['nameComplete']
            sku = product['itemId']
            variation_url = url + '?skuId=' + sku
            stock = json_product['$' + variation_key +
                                 '.sellers.0.commertialOffer'][
                'AvailableQuantity']
            price = Decimal(json_product['$' + variation_key +
                                         '.sellers.0.commertialOffer'][
                                'Price'])

            if not stock and not price:
                return []

            picture_urls = [
                json_product[image['id']]['imageUrl'].split('?v=')[0] for
                image in product['images']]
            p = Product(
                name,
                cls.__name__,
                category,
                variation_url,
                variation_url,
                sku,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                picture_urls=picture_urls,

            )
            products.append(p)
            index += 1
        return products

    @classmethod
    def preflight(cls, extra_args=None):
        return vtex_preflight(
            extra_args, 'https://www.motorola.cl/smartphones/d')
