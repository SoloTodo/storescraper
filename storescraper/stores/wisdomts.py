from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import KEYBOARD, MONITOR, NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Wisdomts(Store):
    @classmethod
    def categories(cls):
        return [
            KEYBOARD,
            MONITOR,
            NOTEBOOK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accessories', KEYBOARD],
            ['monitores', MONITOR],
            ['notebooks', NOTEBOOK]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://wisdomts.cl/tienda/?yith_wcan=1' \
                          '&product_cat={}'.format(url_extension)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('ul', 'products')[-1]

            for container in product_containers.findAll(
                    'li', 'product-grid-view'):
                product_url = container.find('a')['href']
                if '2021-dell-gold-partner' not in product_url:
                    product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        if soup.find('p', 'price').find('ins'):
            price = Decimal(remove_words(
                soup.find('p', 'price').find('ins').text.replace('.', '')))
        else:
            price = Decimal(remove_words(
                soup.find('p', 'price').text.replace('.', '')))
        picture_urls = [tag['data-src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]
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
