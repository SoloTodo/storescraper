import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Fama(Store):
    @classmethod
    def categories(cls):
        return [
            WASHING_MACHINE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            WASHING_MACHINE
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow')
                url_webpage = 'https://www.fama.com.uy/lg?pagenumber={}' \
                    .format(page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'item-box')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category')
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.fama.com.uy' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', {'itemprop': 'name'}).text
        sku = soup.find('div', {'id': 'product-ribbon-info'})['data-productid']
        stock = -1
        price = Decimal(soup.find('span', {'itemprop': 'price'}).text.strip()
                        .split()[1].replace('.', '').replace(',', '.'))

        picture_urls = [tag['src'].replace('_100.jpeg', '.jpeg') for tag in
                        soup.find('div', 'picture-thumbs').findAll('img')
                        ]
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
            'USD',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
