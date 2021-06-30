import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy
from storescraper.categories import TELEVISION


class PlazaLama(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only interested in LG products
        session = session_with_proxy(extra_args)
        product_urls = []

        if category != TELEVISION:
            return []

        page = 1

        while True:
            if page >= 10:
                raise Exception('Page overflow')

            url = 'https://plazalama.com.do/450-electrodomesticos?q=Marca-LG' \
                  '&page={}'.format(page)
            print(url)

            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.findAll('div', 'js-product-miniature-wrapper')

            if not items:
                if page == 1:
                    logging.warning('Empty category:' + url)
                break

            for item in items:
                path = item.find('a')['href'].split('?')[0]
                product_urls.append(path)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        if response.status_code == 404 or response.url != url:
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        product_container = soup.find('div', {'id': 'main-product-wrapper'})
        name = product_container.find('h1', 'h1 page-title').text
        sku = \
            product_container.find('input', {'id': 'product_page_product_id'})[
                'value']
        stock = -1
        price = Decimal(
            product_container.find('span', 'product-price')['content'])
        if product_container.find('div', 'product-images'):
            picture_urls = [tag['src'] for tag in
                            product_container.find('div',
                                                   'product-images').findAll(
                                'img')]
        else:
            picture_urls = [tag['src']
                            for tag in product_container.find('div',
                                                              'product'
                                                              '-images-large'
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
            'DOP',
            sku=sku,
            picture_urls=picture_urls,
        )

        return [p]
