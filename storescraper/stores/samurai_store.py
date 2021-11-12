import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import RAM, VIDEO_CARD, SOLID_STATE_DRIVE, \
    MOUSE, CELL, CPU_COOLER, NOTEBOOK, PROCESSOR, MOTHERBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class SamuraiStore(Store):
    @classmethod
    def categories(cls):
        return [
            RAM,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            MOUSE,
            CELL,
            CPU_COOLER,
            NOTEBOOK,
            PROCESSOR,
            MOTHERBOARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['ram', RAM],
            ['ram-notebook', RAM],
            ['tarjetas-graficas', VIDEO_CARD],
            ['unidades-de-estado-solido', SOLID_STATE_DRIVE],
            ['perifericos', MOUSE],
            ['apple/iphone/iphone-13', CELL],
            ['apple/iphone/iphone-13-mini', CELL],
            ['apple/iphone/iphone-13-pro', CELL],
            ['apple/iphone/iphone-13-pro-max', CELL],
            ['cooler-cpu', CPU_COOLER],
            ['notebook', NOTEBOOK],
            ['procesador', PROCESSOR],
            ['placa-madre', MOTHERBOARD],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 30:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.samuraistorejp.cl/' \
                              'product-category/{}/page/{}/'.format(
                                url_extension, page)
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

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-title').text.strip()

        if 'RIFA' in name:
            return []

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        sku_tag = soup.find('span', 'sku')

        if sku_tag:
            sku = sku_tag.text.strip()
        else:
            sku = None

        if 'preventa' in name.lower():
            stock = 0
        elif soup.find('p', 'stock out-of-stock'):
            stock = 0
        elif soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = -1
        price_container = soup.find('div', 'product-stacked-info').find(
            'table').findAll('bdi')
        normal_price = Decimal(remove_words(price_container[0].text))
        offer_price = Decimal(remove_words(price_container[1].text))
        picture_urls = [tag.find('a')['href'] for tag in soup.find('div',
                        'product-gallery').findAll('div',
                        'woocommerce-product-gallery__image')]
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
            picture_urls=picture_urls
        )
        return [p]
