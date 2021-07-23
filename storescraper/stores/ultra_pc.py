import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, NOTEBOOK, TABLET, CELL, \
    SOLID_STATE_DRIVE, PROCESSOR, RAM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class UltraPc(Store):

    @classmethod
    def categories(cls):
        return [
            ALL_IN_ONE,
            NOTEBOOK,
            TABLET,
            CELL,
            SOLID_STATE_DRIVE,
            PROCESSOR,
            RAM
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computadores-de-escritorio/all-in-one', ALL_IN_ONE],
            ['laptop', NOTEBOOK],
            ['tablets-e-ipads', TABLET],
            ['smartphones', CELL],
            ['almacenamiento-solido', SOLID_STATE_DRIVE],
            ['procesadores', PROCESSOR],
            ['memorias-ram', RAM]
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
                url_webpage = 'https://www.ultrapc.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-outer')
                if not product_containers or soup.find('div', 'info-404'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for container in product_containers:
                    product_url = \
                        container.find('a', 'woocommerce-LoopProduct-link')[
                            'href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'type': 'application/json'})['href'].split(
            '/')[-1]
        if soup.find('span', 'electro-stock-availability').find('p', 'stock'):
            stock = -1
        normal_price = Decimal(
            remove_words(soup.find('div', 'precios_iva').text.split()[0]))
        offer_price = Decimal(
            remove_words(soup.find('span', 'electro-price').find('bdi').text))
        picture_urls = [tag['src'] for tag in soup.find('div',
                                                        'woocommerce'
                                                        '-product'
                                                        '-gallery').findAll(
            'img')]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
