import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import KEYBOARD, CELL, MONITOR, MOTHERBOARD, \
    HEADPHONES, STEREO_SYSTEM, COMPUTER_CASE, SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, GAMING_CHAIR, RAM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Ampera(Store):
    @classmethod
    def categories(cls):
        return {
            KEYBOARD,
            CELL,
            MONITOR,
            MOTHERBOARD,
            HEADPHONES,
            STEREO_SYSTEM,
            COMPUTER_CASE,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            GAMING_CHAIR,
            RAM
        }

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['mouse-y-teclados', KEYBOARD],
            ['celulares-y-tablets', CELL],
            ['monitores', MONITOR],
            ['placas-madre', MOTHERBOARD],
            ['audifonos', HEADPHONES],
            ['parlantes', STEREO_SYSTEM],
            ['gabinetes', COMPUTER_CASE],
            ['ssd', SOLID_STATE_DRIVE],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['discos-duros-internos', STORAGE_DRIVE],
            ['otros', GAMING_CHAIR],
            ['almacenamiento', RAM]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.ampera.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a', 'woocommerce-Loop'
                                                      'Product-link')['href']
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
        sku = str(json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)['sku'])
        if soup.find('p', 'stock').text == 'Agotado':
            stock = 0
        else:
            stock = int(soup.find('p', 'stock').text.split()[0])
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))
        picture_urls = [
            soup.find('div', 'woocommerce-product-gallery__image').find('img')[
                'src']]
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
