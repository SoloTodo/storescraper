import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import KEYBOARD, CELL, MONITOR, MOTHERBOARD, \
    HEADPHONES, STEREO_SYSTEM, COMPUTER_CASE, SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, GAMING_CHAIR, RAM, VIDEO_CARD, \
    PROCESSOR, MOUSE, POWER_SUPPLY, CPU_COOLER, MICROPHONE, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Ampera(Store):
    @classmethod
    def categories(cls):
        return [
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
            RAM,
            VIDEO_CARD,
            PROCESSOR,
            MOUSE,
            POWER_SUPPLY,
            CPU_COOLER,
            MICROPHONE,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['teclados', KEYBOARD],
            ['mouse', MOUSE],
            ['celulares-y-tablets', CELL],
            ['monitores', MONITOR],
            ['placas-madre', MOTHERBOARD],
            ['audifonos', HEADPHONES],
            ['parlantes', STEREO_SYSTEM],
            ['gabinetes', COMPUTER_CASE],
            ['ssd', SOLID_STATE_DRIVE],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['discos-duros-internos', STORAGE_DRIVE],
            ['sillas', GAMING_CHAIR],
            ['ram', RAM],
            ['gpus', VIDEO_CARD],
            ['procesadores', PROCESSOR],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['refrigeracion/refrigeracion-aire', CPU_COOLER],
            ['refrigeracion/refrigeracion-liquida', CPU_COOLER],
            ['refrigeracion/ventiladores', CASE_FAN],
            ['microfonos', MICROPHONE]
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
                    product_url = product_url.replace('/producto/', '/tienda/')
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.url != url:
            print(response.url)
            print(url)
            return []

        print('pass')

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        if soup.find('form', 'variations_form'):
            products = []
            variations = json.loads(soup.find('form', 'variations_form')[
                                        'data-product_variations'])
            for product in variations:
                variation_name = name + ' - ' + product['attributes'][
                    'attribute_pa_color']
                sku = str(product['variation_id'])
                if product['max_qty'] == '':
                    stock = 0
                else:
                    stock = product['max_qty']
                price = Decimal(product['display_price'])
                picture_urls = [product['image']['url']]
                p = Product(
                    variation_name,
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
                products.append(p)
            return products
        else:
            sku = str(json.loads(
                soup.find('script', {'type': 'application/ld+json'})
                    .text)['sku'])
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
                soup.find('div', 'woocommerce-product-gallery__image')
                    .find('img')['src']]
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
