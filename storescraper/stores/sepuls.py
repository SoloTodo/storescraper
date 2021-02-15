import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, KEYBOARD, HEADPHONES, \
    MONITOR, MOUSE, STEREO_SYSTEM, COMPUTER_CASE, MOTHERBOARD, PROCESSOR, \
    VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Sepuls(Store):
    @classmethod
    def categories(cls):
        return [
            GAMING_CHAIR,
            KEYBOARD,
            HEADPHONES,
            MONITOR,
            MOUSE,
            STEREO_SYSTEM,
            COMPUTER_CASE,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['sillas', GAMING_CHAIR],
            ['teclados', KEYBOARD],
            ['audifonos', HEADPHONES],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['parlantes', STEREO_SYSTEM],
            ['gabinetes', COMPUTER_CASE],
            ['placa-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['tarjetas-de-video', VIDEO_CARD]
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
                url_webpage = 'https://www.sepuls.cl/{}/page/{}/'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-grid-item')
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
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'alternate'})['href'].split('/')[-1]
        if soup.find('p', 'stock').text == 'SIN STOCK':
            stock = 0
        else:
            stock = -1
        if soup.find('p', 'price').text == '':
            return []
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))
        picture_urls = [tag['src'] for tag in soup.find('div', 'woocommerce'
                                                               '-product'
                                                               '-gallery'
                                                               '').findAll(
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
