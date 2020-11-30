from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import REFRIGERATOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MartinArismendi(Store):
    @classmethod
    def categories(cls):
        return [
            REFRIGERATOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            REFRIGERATOR
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://martinarismendi.com.uy/marca/lg/'
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.find('ul', 'products')
            if not product_containers:
                break
            for container in product_containers.findAll('li'):
                product_url = container.find('a')['href']
                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('button', 'single_add_to_cart_button')['value']
        if soup.find('p', 'stock').text.split(':')[1] == 'Hay existencias':
            stock = - 1
        else:
            stock = 0
        price = Decimal(soup.find('bdi').text.split()[-1].replace(',', ''))
        picture_urls = [
            soup.find('div', 'woocommerce-product-gallery').find('img')['src']]
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
            picture_urls=picture_urls
        )
        return [p]
