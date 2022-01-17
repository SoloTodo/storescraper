import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD, GAMING_CHAIR, MOUSE, \
    COMPUTER_CASE, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class KrakenStore(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_CARD,
            GAMING_CHAIR,
            MOUSE,
            COMPUTER_CASE,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['tarjetas-graficas', VIDEO_CARD],
            ['componentes', COMPUTER_CASE],
            ['monitores', MONITOR],
            ['sillas-gamer', GAMING_CHAIR],
            ['perifericos', MOUSE]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://www.krakenstore.cl/{}/' \
                .format(url_extension)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.find(
                'div', {'id': 'product_list'}).findAll('a', 'text-reset')
            if not product_containers:
                logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = container['href']
                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_container = soup.find('div', 'row pt-2')
        name = product_container.find('h1', 'h3').text
        sku = product_container.find('input', {'name': 'product_id'})['value']
        if product_container.find('button', {'name': 'bag_add'}).text == \
                'No disponible':
            stock = 0
        else:
            stock = -1
        price = Decimal(
            remove_words(product_container.find('p', 'd-inline lead').text))
        picture_urls = [tag['src'] for tag in
                        product_container.find('div', 'col-md-6 mb-2').findAll(
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
