import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, RAM, MOTHERBOARD, PROCESSOR, \
    SOLID_STATE_DRIVE, TELEVISION, VIDEO_CARD, CPU_COOLER, WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class PcBoost(Store):
    @classmethod
    def categories(cls):
        return [
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            CPU_COOLER,
            CELL,
            TELEVISION,
            WEARABLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['memorias-ram', RAM],
            ['placas-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['ssd', SOLID_STATE_DRIVE],
            ['tarjetas-de-video', VIDEO_CARD],
            ['disipadores', CPU_COOLER],
            ['smartphones', CELL],
            ['televisores', TELEVISION],
            ['wearables', WEARABLE],
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
                url_webpage = 'https://www.pcboost.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-small')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-title').text.strip()
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        price_container = soup.find('p', 'price')
        if not price_container.find('del'):
            normal_price = Decimal(
                remove_words(price_container.find('bdi').text))
            offer_price = normal_price
        else:
            normal_price = Decimal(
                remove_words(
                    price_container.find('del').find('span', 'woocommerce'
                                                             '-Price'
                                                             '-amount').
                    text))
            offer_price = Decimal(remove_words(
                price_container.find('ins').find('span', 'woocommerce-Price'
                                                         '-amount').text))
        picture_urls = [tag['src'] for tag in soup.find('div',
                                                        'product-images').
                        findAll('img')]
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
