import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, magento_picture_urls
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
        if TELEVISION != category:
            return []

        page = 1
        while True:
            if page >= 30:
                raise Exception('Page overflow')

            url = 'https://plazalama.com.do/catalogsearch/result/?marca=368&q=LG+LG' \
                '&p={}'.format(page)
            print(url)
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html5lib')
            product_containers = soup.findAll('li', 'product-item')

            if not product_containers:
                if page == 1:
                    logging.warning('Empty category:' + url)
                break

            for container in product_containers:
                product_url = container.find('a', 'product')['href']
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')

        name = soup.find('span', {'itemprop': 'name'}).text.strip()
        description = soup.find('div', {'id': 'product.specifications'}).text.strip()
        key = soup.find('input', {'name': 'product'})['value']
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()
        price = Decimal(soup.find('meta', {'itemprop': 'price'})['content'])
        picture_urls = magento_picture_urls(soup)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            -1,
            price,
            price,
            'DOP',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
