import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD, NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Dgital(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_CARD,
            NOTEBOOK,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['3-amd', VIDEO_CARD],
            ['6-nvidia', VIDEO_CARD],
            ['9-macbooks', NOTEBOOK],
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

                url_webpage = 'https://dgital.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'products row')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('div', {
                        'itemprop': 'itemListElement'}):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'h1').text
        sku = soup.find('input', {'name': 'id_product'})['value']
        price = Decimal(soup.find('span', {'itemprop': 'price'})['content'])
        stock = -1
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
