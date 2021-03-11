import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import REFRIGERATOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class SendTech(Store):
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
        products_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception('page overflow')
                url_webpage = 'https://sendtech.cl/page/' \
                              '{}/?s=SAMSUNG&post_type=product'.format(page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                products_containers = soup.find('ul', 'products')
                if not products_containers:
                    if page == 0:
                        logging.warning('Empty category: ' + local_category)
                    break
                for container in products_containers.findAll('li'):
                    products_url = container.find('a')['href']
                    products_urls.append(products_url)
                page += 1
        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        if soup.find('p', 'stock in-stock'):
            stock = -1
        else:
            stock = 0
        if soup.find('p', 'price').text == '':
            return []
        elif soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))
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
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
