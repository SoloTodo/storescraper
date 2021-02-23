import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, HEADPHONES, \
    COMPUTER_CASE, RAM, PROCESSOR, VIDEO_CARD, MOTHERBOARD, GAMING_CHAIR, \
    KEYBOARD, POWER_SUPPLY, CPU_COOLER, MONITOR, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class GWStore(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            HEADPHONES,
            COMPUTER_CASE,
            RAM,
            PROCESSOR,
            VIDEO_CARD,
            MOTHERBOARD,
            GAMING_CHAIR,
            KEYBOARD,
            POWER_SUPPLY,
            CPU_COOLER,
            MONITOR,
            MOUSE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['Almacenamiento', SOLID_STATE_DRIVE],
            ['audio-y-video', HEADPHONES],
            ['gabinete', COMPUTER_CASE],
            ['memorias', RAM],
            ['proce', PROCESSOR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['placas-madres', MOTHERBOARD],
            ['accesorios/sillas-gamer', GAMING_CHAIR],
            ['accesorios/teclados-gamer', KEYBOARD],
            ['cougar', POWER_SUPPLY],
            ['enfriamiento/cpu-cooler', CPU_COOLER],
            ['enfriamiento/enfriamiento-liquido', CPU_COOLER],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['monitores', MONITOR],
            ['perifericos/audifonos-perifericos', HEADPHONES],
            ['perifericos/mouse', MOUSE],
            ['perifericos/teclados', KEYBOARD],
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
                url_webpage = 'https://gwstore.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('ul', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll(
                        'li', 'type-product'):
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
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[1]

        stock_container = soup.find('p', 'stock')
        if stock_container and 'Agotado' in stock_container.text:
            stock = 0
        elif stock_container and 'In stock' in stock_container.text:
            stock = -1
        else:
            stock = int(stock_container.contents[1].split()[0])
        price = Decimal(remove_words(soup.find(
            'span', 'woocommerce-Price-amount').find('bdi').contents[1]))
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'woocommerce-tabs').findAll('img')]
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
