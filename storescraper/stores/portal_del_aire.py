import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import AIR_CONDITIONER


class PortalDelAire(StoreWithUrlExtensions):
    url_extensions = [
        ['aire-acondicionado-mini-split', AIR_CONDITIONER],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        page = 1

        while True:
            if page > 10:
                raise Exception('Page overflow')

            url = 'https://portaldelaire.cl/collections/{}?page={}'\
                .format(url_extension, page)
            print(url)
            response = session.get(url)

            soup = BeautifulSoup(response.text, 'html.parser')
            products_container = soup.find('div', 'product-list')
            products = products_container.findAll('div', 'product-item')

            if not products:
                break

            for product in products:
                product_url = ('https://portaldelaire.cl' +
                               product.find('a',
                                            'product-item__title')['href'])
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        product_data = json.loads(soup.findAll(
            'script', {'type': 'application/json'})[-1].text)
        description = html_to_markdown(product_data['product']['description'])
        picture_urls = ['https:' + x for x in
                        product_data['product']['images']]

        products = []

        for variant in product_data['product']['variants']:
            name = variant['name']
            key = str(variant['id'])
            sku = variant['sku'] or None
            stock = product_data['inventories'][key]['inventory_quantity']
            price = Decimal(variant['price'] / 100)

            p = Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                part_number=sku,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
