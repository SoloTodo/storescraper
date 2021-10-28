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
        local_categories = [
            TELEVISION
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in local_categories:
            if local_category != category:
                continue
            page = 1
            if page > 10:
                raise Exception('page overlfow: ' + local_category)
            url_webpage = 'https://gadtecnology.com/shop/'
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('li', 'product')

            if not product_containers:
                if page == 1:
                    logging.warning('empty category: ' + local_category)
                break
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)
            page += 1
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
