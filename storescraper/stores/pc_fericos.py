import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, CPU_COOLER, KEYBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class PcFericos(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            CPU_COOLER,
            KEYBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['gabinetes', COMPUTER_CASE],
            ['refrigeracion', CPU_COOLER],
            ['refrigeracion-por-aire', CPU_COOLER],
            ['teclados', KEYBOARD]
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

                url_webpage = 'https://pcfericos.cl/collections/{}?page={}' \
                    .format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('a', 'product-block-title')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['href']
                    product_urls.append('https://pcfericos.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        import ipdb
        ipdb.set_trace()
        name = soup.find('h1', 'product-title').text
        sku = soup.find('div', 'productoptions').find('input', {'name': 'id'})[
            'value']
        json_container = json.loads(soup.find('script', {'type': 'application/ld+json'}).text)
        if json_container['offers'][0][
            'availability'] == 'http://schema.org/OutOfStock':
            stock = 0
        else:
            stock = -1
        price = Decimal(json_container['offers'][0]['price'])
        picture_urls = []
        for tag in soup.find('div', 'gallery-thumbs').findAll('img'):
            if tag.get('src'):
                picture_urls.append('https:' + tag['src'])
            else:
                picture_urls.append('https:' +
                                    tag['data-src'].replace('_{width}x',
                                                            '').split('?')[0])

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
            picture_urls=picture_urls,
        )
        return [p]
