import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD, MOUSE, VIDEO_GAME_CONSOLE, CELL
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Yokan(StoreWithUrlExtensions):
    url_extensions = [
        ['apple', CELL],
        ['tecno/consolas', VIDEO_GAME_CONSOLE],
        ['tecno/tvid', VIDEO_CARD],
        ['tecno/mouse', MOUSE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('Page overflow')
            url_webpage = 'https://yokan.cl/product-category/{}/page/{}'\
                .format(url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('div', 'product-small')

            if not product_containers:
                if page == 1:
                    logging.warning('empty category: ' + url_extension)
                break

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)
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
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-title').text.strip()
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        sku_tag = soup.find('span', 'sku')

        if sku_tag:
            sku = soup.find('span', 'sku').text.strip()
        else:
            sku = None

        if soup.find('p', 'available-on-backorder'):
            stock = 0
        elif soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock').text.strip().split()[0])
        else:
            stock = -1

        price_container = soup.find('p', 'price')
        if price_container.find('ins'):
            offer_price = Decimal(remove_words(
                price_container.find('ins').text.strip()))
        else:
            offer_price = Decimal(remove_words(
                price_container.text.strip()))

        normal_price = (offer_price * Decimal('1.05')).quantize(0)

        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'product-gallery').findAll('img')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls)
        return [p]