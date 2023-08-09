import logging

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Multimax(Store):
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
        product_urls = []
        page = 1
        while True:
            if page >= 20:
                raise Exception('Page overflow')

            url_webpage = ('https://www.multimax.net/collections/lg?page={}'
                           ).format(page)

            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.findAll('div', 'product__grid-item')

            if len(items) == 0:
                if page == 1:
                    logging.warning('Empty category')
                break

            for item in items:
                product_urls.append(
                    'https://www.multimax.net' + item.find('a')['href'])

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_name').text.strip()
        sku = soup.find('div', 'clearfix')['data-product-id']
        stock = -1
        price = Decimal(soup.find('div', 'modal_price subtitle').find('span',
                                                                      'money')
                        .text.replace('$', '').replace(',', ''))
        picture_urls = ['https:' + tag['src'] for tag in soup.find('div',
                                                                   'product-'
                                                                   'gallery')
                        .findAll('img', 'lazyloaded')]
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
