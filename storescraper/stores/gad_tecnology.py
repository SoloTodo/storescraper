import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class GadTecnology(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        if category != TELEVISION:
            return []

        url_webpage = 'https://gadtecnology.com/shop/'
        response = session.get(url_webpage)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_containers = soup.findAll('li', 'product')

        if not product_containers:
            logging.warning('empty category')

        for container in product_containers:
            product_url = container.find('a')['href']
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('title').text.split('-')[0].strip()
        sku = soup.find('button', {'name': 'add-to-cart'})['value']
        stock = -1
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                soup.find('p', 'price').find('ins').text.replace('$',
                                                                 '').replace(
                    ',', ''))
        else:
            price = Decimal(
                soup.find('p', 'price').text.replace('$', '').replace(',', ''))
        picture_urls = [tag['src'] for tag in soup.find('div', 'woocommerce'
                                                               '-product'
                                                               '-gallery'
                                                               '').findAll(
            'img')]
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
        )
        return [p]
