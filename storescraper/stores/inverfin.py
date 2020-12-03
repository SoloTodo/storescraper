from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Inverfin(Store):
    base_url = 'https://www.lg.com'
    country_code = 'cl'

    @classmethod
    def categories(cls):
        return [
            'Television',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        if category != 'Television':
            return []

        page = 1

        while True:
            url = 'https://inverfin.com.py/search?type=product&q=LG*&page=' + \
                  str(page)

            if page >= 15:
                raise Exception('Page overflow' + url)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            product_containers = soup.findAll('div', 'product-item')

            if not product_containers:
                if page == 1:
                    raise Exception('Empty category: ' + url)
                break

            for product in product_containers:
                product_link = product.find('a', 'product-item__title')

                if 'LG' not in product_link.text.upper():
                    continue

                product_url = 'https://inverfin.com.py{}'.format(
                    product_link['href'])
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        if 'Liquid error' in soup.text:
            return []

        name = soup.find('h1', 'product-meta__title').text.strip()
        sku = soup.find('span', 'product-meta__sku-number').text.strip()
        stock = -1

        if 'LG' not in name.upper().split(' '):
            stock = 0

        if not soup.find('span', {'id': 'cash-price'}):
            return []

        price = Decimal(
            soup.find('span', {'id': 'cash-price'}).text.replace('Gs.', '')
                .replace('.', '').strip())

        pictures = soup.findAll('img', 'product-gallery__image')
        picture_urls = []

        for picture in pictures:
            picture_url = 'https:' + picture['data-zoom']
            picture_urls.append(picture_url)

        return [Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'PYG',
            sku=sku,
            picture_urls=picture_urls
        )]
