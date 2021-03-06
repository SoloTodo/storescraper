import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MOTHERBOARD, PROCESSOR, \
    VIDEO_CARD, COMPUTER_CASE, STORAGE_DRIVE, RAM, GAMING_CHAIR, MOUSE, \
    KEYBOARD, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class GoldenGamers(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            COMPUTER_CASE,
            STORAGE_DRIVE,
            RAM,
            GAMING_CHAIR,
            MOUSE,
            KEYBOARD,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['componentes/Tipo_Placa-Madre', MOTHERBOARD],
            ['componentes/Tipo_CPU', PROCESSOR],
            ['componentes/Tipo_Tarjeta-de-Video', VIDEO_CARD],
            ['componentes/Tipo_Gabinete', COMPUTER_CASE],
            ['componentes/Tipo_Disco-Duro', STORAGE_DRIVE],
            ['componentes/Tipo_Memoria-RAM', RAM],
            ['silla-gamer', GAMING_CHAIR],
            ['mouse-gamer', MOUSE],
            ['teclados', KEYBOARD],
            ['monitores', MONITOR],
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
                url_webpage = 'https://goldengamers.cl/collections/' \
                              '{}?page={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'container-pushy-main') \
                    .findAll('div', 'col-md-4')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://goldengamers.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_container = soup.find('div', {'id': 'parent'})
        name = product_container.find('h1', 'product-item-caption-title').text
        sku = product_container.find('span', 'shopify-product-reviews-badge')[
            'data-id']
        stock_container = product_container.find('div', {
            'id': 'variant-inventory'}).text.strip().split()[2]
        if stock_container.isnumeric():
            stock = int(stock_container)
        else:
            stock = 0
        price = Decimal(remove_words(
            product_container.find('ul', 'product-item-caption-price').find(
                'li', 'product-item-caption-price-current').text.replace('CLP',
                                                                         '')))
        picture_urls = [
            'https:' + tag['src'].replace('_small', '').split('?')[0] for tag
            in product_container.find('div', 'swiper-horiz-'
                                             'thumbnails-main-container').
            findAll('img')]
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
