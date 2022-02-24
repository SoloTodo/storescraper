import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, VIDEO_CARD, PROCESSOR, \
    MOTHERBOARD, RAM, SOLID_STATE_DRIVE, POWER_SUPPLY, CPU_COOLER, KEYBOARD, \
    MOUSE, GAMING_CHAIR, MONITOR, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class MancoStore(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            VIDEO_CARD,
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            CPU_COOLER,
            KEYBOARD,
            MOUSE,
            MONITOR,
            GAMING_CHAIR,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['gabinetes', COMPUTER_CASE],
            ['almacenamiento', SOLID_STATE_DRIVE],
            ['procesadores', PROCESSOR],
            ['memorias', RAM],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['placas-madre', MOTHERBOARD],
            ['tarjetas-de-video', VIDEO_CARD],
            ['refrigeracion', CPU_COOLER],
            ['perifericos/mouse', MOUSE],
            ['perifericos/teclados', KEYBOARD],
            ['monitores', MONITOR],
            ['perifericos/sillas-gamer', GAMING_CHAIR],
            ['perifericos/auriculares-y-mic', HEADPHONES]
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://mancostore.cl/categoria-producto/{}' \
                              '/page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
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
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-title').text.strip()
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        elif soup.find('p', 'stock out-of-stock'):
            stock = 0

        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))

        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'product-gallery').findAll('img')]
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
