import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, TELEVISION, STEREO_SYSTEM, \
    REFRIGERATOR, WASHING_MACHINE, AIR_CONDITIONER, OVEN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class ElGalloMasGallo(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            TELEVISION,
            STEREO_SYSTEM,
            REFRIGERATOR,
            WASHING_MACHINE,
            OVEN,
            AIR_CONDITIONER,

        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            [
                '%5B%22marca%3ALG%22%2C%5B%22categories.level1%3AProductos'
                '%20%2F%2F%2F%20Celulares%20%7C%20Tablets%22%5D%5D',
                CELL],
            [
                '%5B%22marca%3ALG%22%2C%5B%22categories.level1%3AProductos'
                '%20%2F%2F%2F%20TV%20y%20Video%22%5D%5D',
                TELEVISION],
            [
                '%5B%22marca%3ALG%22%2C%5B%22categories.level1%3AProductos'
                '%20%2F%2F%2F%20Audio%22%5D%5D',
                STEREO_SYSTEM],
            [
                '%5B%22marca%3ALG%22%2C%5B%22categories.level2%3AProductos'
                '%20%2F%2F%2F%20Hogar%20y%20L%C3%ADnea%20Blanca%20%2F%2F%2F'
                '%20Refrigeradoras%22%5D%5D',
                REFRIGERATOR],
            [
                '%5B%22marca%3ALG%22%2C%5B%22categories.level2%3AProductos'
                '%20%2F%2F%2F%20Hogar%20y%20L%C3%ADnea%20Blanca%20%2F%2F%2F'
                '%20Lavadoras%20y%20secadoras%22%5D%5D',
                WASHING_MACHINE],
            [
                '%5B%22marca%3ALG%22%2C%5B%22categories.level2%3AProductos'
                '%20%2F%2F%2F%20Hogar%20y%20L%C3%ADnea%20Blanca%20%2F%2F%2F'
                '%20Hornos%20y%20extractores%22%5D%5D',
                OVEN],
            [
                '%5B%22marca%3ALG%22%2C%5B%22categories.level2%3AProductos'
                '%20%2F%2F%2F%20Hogar%20y%20L%C3%ADnea%20Blanca%20%2F%2F%2F'
                '%20Aires%20acondicionados%20%7C%20Purificadores%22%5D%5D',
                AIR_CONDITIONER],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 0
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                body = json.dumps({
                    "requests": [
                        {
                            "indexName": "monge_prod_elgallo_ni_products",
                            "params": "query=&hitsPerPage=9&maxValuesPerFacet="
                                      "40&page={}&"
                                      "facetFilters={}".format(
                                        page, url_extension)
                        }
                    ]
                })
                url_webpage = r'https://wlt832ea3j-dsn.algolia.net/1/indexes' \
                              '/*/queries?x-algolia-application-id' \
                              '=WLT832EA3J&x-algolia-api-key' \
                              '=MjQyMGI4YWYzNWJkNzg5OTIxMmRkYTljY2ZmNDkyOD' \
                              'NmMmZmNGU1NWRkZWU3NGE3MjNhYmNmZWZhOWFmNmQ0M3' \
                              'RhZ0ZpbHRlcnM9'
                print(url_webpage)
                response = session.post(url_webpage, data=body)
                product_json = json.loads(response.text)['results'][0]['hits']

                if not product_json:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break
                for product in product_json:
                    product_url = product['url']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'page-title').text.strip()
        sku = soup.find('form', {'id': 'product_addtocart_form'})[
            'data-product-sku']
        stock = -1
        price = Decimal(
            soup.find('span', 'price').text.split('C$')[1].replace(',', ''))
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'product media').findAll('img')]
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
            'NIO',
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
