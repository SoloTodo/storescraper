import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import REFRIGERATOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MegaStore(Store):
    @classmethod
    def categories(cls):
        return [
            REFRIGERATOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['lg', REFRIGERATOR]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                url_webpage = 'https://www.megastore.com.uy/{}?pageNumber={}' \
                              ''.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'item-box')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.megastore.com.uy' + product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('div', 'sku').find('span',
                                            'value').text + ' - ' + soup.find(
            'div', 'product-name').text.strip()
        sku = soup.find('div', 'sku').find('span', 'value')['id'].split('-')[1]
        stock = -1
        price_container = soup.find('span', {'itemprop': 'price'}).text.split()
        price = Decimal(price_container[1].replace('.', ''))
        currency = 'USD' if price_container[0] == 'U$S' else 'UYU'
        picture_urls = [tag['src'].split('.jpeg')[0][:-4] + '.jpeg' for tag in
                        soup.find('div', 'gallery').findAll('img')]
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
            currency,
            sku=sku,
            picture_urls=picture_urls

        )
        return [p]
