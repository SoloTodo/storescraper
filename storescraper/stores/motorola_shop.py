import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MotorolaShop(Store):
    @classmethod
    def categories(cls):
        return [
            CELL
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['smartphones/d', CELL]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://www.motorola.cl/{}'.format(
                url_extension)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('div',
                                              'vtex-search-result-3-'
                                              'x-galleryItem')
            if not product_containers:
                logging.warning('empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append('https://www.motorola.cl' + product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        product_container = re.search(r'__STATE__ = {(.+)}',
                                      response.text).groups()[0]

        json_product = json.loads('{' + product_container + '}')
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
