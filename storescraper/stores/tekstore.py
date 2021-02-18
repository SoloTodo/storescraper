import logging
from bs4 import BeautifulSoup
from decimal import Decimal
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Tekstore(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Tablet',
            'Headphones',
            'Wearable'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ('smartphones', 'Cell'),
            ('tablets', 'Tablet'),
            ('accesorios', 'Headphones')
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            done = False
            while not done:
                if page > 10:
                    raise Exception('Page overflow')

                url_webpage = 'https://tekstore.cl/collections/{}?p={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div',
                                                  'grid-product__wrapper')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    if container.find('div', 'grid-product__sold-out'):
                        continue
                    product_url = container.find('a', 'grid-product__meta')[
                        'href']
                    if 'https://tekstore.cl' + product_url in product_urls:
                        done = True
                        break
                    product_urls.append('https://tekstore.cl' + product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'

        response = session.get(url)
        if response.status_code == 404:
            return []
        data = response.text
        soup = BeautifulSoup(data, 'html.parser')
        name = soup.find('h1', "product-single__title").text.strip()
        sku = soup.find('option')['value']
        stock = -1
        price = Decimal(soup.find('span', {'id': 'ProductPrice'})['content'])
        picture_urls = ['http:' + tag.find('img')['src'] for tag in
                        soup.findAll('li', 'grid__item')]
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
