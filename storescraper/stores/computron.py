import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Computron(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            TELEVISION
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow')
                url_webpage = 'https://computron.com.ec/efectivo/' \
                              'catalogsearch/' \
                              'result/index/?p={}&q=LG+LG'.format(page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-item-info')
                if not product_containers:
                    if page == 1:
                        logging.warning('empty category')
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in product_urls:
                        continue
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
        part_number = soup.find('div', {'itemprop': 'sku'}).text
        sku = soup.find('input', {'name': 'item'})['value']
        if soup.find('div', 'stock available'):
            stock = -1
        else:
            stock = 0
        price = Decimal(soup.find('span', 'price').text.
                        replace(',', '').replace('$', ''))
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'gallery-placeholder').findAll('img')]
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
            part_number=part_number,
            picture_urls=picture_urls
        )
        return [p]
