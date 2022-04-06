import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Geant(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            TELEVISION
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        page_size = 30
        for local_category in url_extensions:
            if local_category != category:
                continue

            page = 0
            while True:
                if page > 10:
                    raise Exception('Page overflow')
                url_webpage = 'https://www.geant.com.uy/api/catalog_system/' \
                              'pub/products/search/busca?O=OrderByScoreDESC' \
                              '&_from={}&_to={}&fq=B:56&ft=LG'.format(
                                page * page_size,
                                (page + 1) * page_size - 1)
                data = session.get(url_webpage)
                product_containers = data.json()
                if not product_containers:
                    break
                for container in product_containers:
                    product_url = container['linkText']
                    product_urls.append(
                        'https://www.geant.com.uy/' + product_url + '/p')

                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        sku = soup.find('input', {'id': '___rc-p-id'})['value']
        product_info = session.get('https://www.geant.com.uy/api/catalog_'
                                   'system/pub/products/search/'
                                   '?fq=productId:' + sku).json()[0]
        name = product_info['productName']
        stock = product_info['items'][0]['sellers'][0]['commertialOffer'][
            'AvailableQuantity']
        price = Decimal(str(
            product_info['items'][0]['sellers'][0]['commertialOffer'][
                'Price']))
        picture_urls = [
            product_info['items'][0]['images'][0]['imageUrl'].split('?')[0]]
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
            'UYU',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
