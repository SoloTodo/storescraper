from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class ImportacionesRubi(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only gets LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        product_urls = []

        page = 1

        while True:
            if page > 10:
                raise Exception('Page overflow')

            url = 'https://importacionesrubi.com.pe/productos.html?p={}&prod' \
                'uct_brand=112&product_list_limit=36'.format(page)
            print(url)

            response = session.get(url).text
            soup = BeautifulSoup(response, 'html.parser')
            product_containers = soup.findAll('li', 'product')

            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + category)
                break

            for container in product_containers:
                product_url = container.find('a')['href']
                if product_url in product_urls:
                    return product_urls
                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('input', {'name': 'item'})['value']

        name = soup.find('span', {'itemprop': 'name'}).text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()

        if soup.find('div', 'stock available'):
            stock = -1
        else:
            stock = 0

        price = Decimal(
            soup.find('span', {'data-price-type': 'finalPrice'}
                      )['data-price-amount'])

        picture_urls = [soup.find('img', 'gallery-placeholder__image')['src']]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'PEN',
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
