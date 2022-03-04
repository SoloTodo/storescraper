import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, GAMING_CHAIR, MONITOR, \
    COMPUTER_CASE, VIDEO_CARD, GAMING_DESK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Valrod(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            GAMING_CHAIR,
            MONITOR,
            COMPUTER_CASE,
            VIDEO_CARD,
            GAMING_DESK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['perifericos', HEADPHONES],
            ['audifonos', HEADPHONES],
            ['sillas-gamer', GAMING_CHAIR],
            ['accesorios', COMPUTER_CASE],
            ['monitores', MONITOR],
            ['gabinetes', COMPUTER_CASE],
            ['accesorios', COMPUTER_CASE],
            ['tarjeta-de-video-y-coolers', VIDEO_CARD],
            ['escritorios', GAMING_DESK]
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

                url_webpage = 'https://valrod.cl/gamers/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_container = soup.findAll('div', 'product-item large')

                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_container:
                    product_url = container.find('a')['href']
                    product_urls.append('https://valrod.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('div', 'product-name-wrapper').find('h1').text
        key = soup.find('form', {'id': 'addtocart'})['action'].split('/')[-1]
        sku = re.search(r'"sku":\s?"(.+?)"', response.text).groups()[0]
        stock_container = soup.find('div', 'product-availability').find('span')
        if stock_container.text == 'No Disponible' or \
                stock_container.text == 'Agotado':
            stock = 0
        else:
            stock = int(stock_container.text)
        price = Decimal(remove_words(
            soup.find('div', 'price').find('span', 'special-price').text))
        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div', 'product-previews-wrapper').findAll(
                            'img')]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls
        )
        return [p]
