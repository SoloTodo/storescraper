import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, RAM, POWER_SUPPLY, \
    VIDEO_CARD, SOLID_STATE_DRIVE, CPU_COOLER, PROCESSOR, MONITOR, \
    COMPUTER_CASE, HEADPHONES, MOUSE, KEYBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class BulldogPc(Store):
    @classmethod
    def categories(cls):
        return [
            POWER_SUPPLY,
            RAM,
            MOTHERBOARD,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            CPU_COOLER,
            PROCESSOR,
            MONITOR,
            COMPUTER_CASE,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['productos/almacenamiento', SOLID_STATE_DRIVE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['productos/gabinetes', COMPUTER_CASE],
            ['memorias', RAM],
            ['productos/monitores', MONITOR],
            ['productos/placas-madre', MOTHERBOARD],
            ['productos/refrigeracion', CPU_COOLER],
            ['productos/perifericos/audifonos', HEADPHONES],
            ['productos/perifericos/ratones', MOUSE],
            ['productos/perifericos/teclados', KEYBOARD],
            ['productos/procesadores', PROCESSOR],
            ['productos/tarjetas-de-video', VIDEO_CARD],
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
                url_webpage = 'https://www.bulldogpc.cl/categoria-producto/' \
                    '{}/?product-page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = \
                        container.find('a', 'woocommerce-LoopProduct-link '
                                            'woocommerce-loop-product__link'
                                       )['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[-1]

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)['@graph'][0]
        name = json_data['name']
        sku = str(json_data['sku'])
        description = json_data['description']

        stock = 0
        qty_div = soup.find('div', 'quantity')
        if qty_div:
            qty_input = qty_div.find('input')
            if qty_input.has_attr('max'):
                if qty_input['max'] != "":
                    stock = int(qty_input['max'])
                else:
                    stock = -1
            else:
                stock = 1

        price = Decimal(json_data['offers'][0]['price'])

        picture_containers = soup.find(
            "figure", "woocommerce-product-gallery__wrapper")
        if picture_containers:
            picture_urls = [tag['href'] for tag in
                            picture_containers.findAll('a')]
        else:
            picture_urls = [json_data['image']]
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
            picture_urls=picture_urls,
            description=description
        )
        return [p]
