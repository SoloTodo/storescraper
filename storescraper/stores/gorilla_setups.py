import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, KEYBOARD, MONITOR, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class GorillaSetups(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            KEYBOARD,
            MONITOR,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['26-mouse-y-mouse-pad', MOUSE],
            ['27-teclados', KEYBOARD],
            ['19-monitores', MONITOR],
            ['28-audifonos', HEADPHONES]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://gorillasetups.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('section', {'id': 'products'}) \
                    .find('div', 'laberProductGrid')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers. \
                        findAll('article', 'product-miniature'):
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
        name = soup.find('h1', {'itemprop': 'name'}).text
        sku = soup.find('input', {'name': 'id_product'})['value']
        stock = -1
        price = Decimal(
            soup.find('div', 'current-price').find('span')['content'])
        picture_urls = [tag['src'] for tag in
                        soup.find('ul', 'product-images').findAll('img')]
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
