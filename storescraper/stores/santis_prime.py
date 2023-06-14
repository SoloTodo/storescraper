from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import COMPUTER_CASE, GAMING_CHAIR, HEADPHONES, \
    KEYBOARD, MOUSE, POWER_SUPPLY, MONITOR, RAM, SOLID_STATE_DRIVE, \
    PROCESSOR, MOTHERBOARD, VIDEO_CARD, CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class SantisPrime(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE, GAMING_CHAIR, HEADPHONES, KEYBOARD, MOUSE,
            POWER_SUPPLY, MONITOR, RAM, SOLID_STATE_DRIVE, PROCESSOR,
            MOTHERBOARD, VIDEO_CARD, CPU_COOLER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['teclados', KEYBOARD],
            ['mouse', MOUSE],
            ['audifonos', HEADPHONES],
            ['accesorios', HEADPHONES],
            ['monitores', MONITOR],
            ['memoriasram', RAM],
            ['almacenamiento', SOLID_STATE_DRIVE],
            ['procesadores', PROCESSOR],
            ['placasmadres', MOTHERBOARD],
            ['tarjetasgraficas', VIDEO_CARD],
            ['fuentespoder', POWER_SUPPLY],
            ['refrigeracion-y-ventiladores', CPU_COOLER],
            ['sillasgamer', GAMING_CHAIR],
            ['gabinetes', COMPUTER_CASE],
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
                url_webpage = 'https://www.santisprimesolution.cl/' \
                              'product-category/{}/page/{}'.format(
                                  url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
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

        name = soup.find('h1', 'product_title').text.strip()
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[-1]
        quantity_tag = soup.find('div', 'quantity')

        if quantity_tag:
            input_stock = quantity_tag.find('input')
            if input_stock['max']:
                stock = int(input_stock['max'])
            else:
                stock = -1
        else:
            stock = 0

        description_tag = soup.find(
            'div', 'woocommerce-product-details__short-description')

        normal_price = Decimal(remove_words(soup.find(
            'div', 'elementor-widget-woocommerce-product-price')
            .findAll('span', 'woocommerce-Price-amount')[1].text))
        offer_price_tag = description_tag.find('h1')

        if offer_price_tag:
            offer_price = Decimal(remove_words(offer_price_tag.text))
        else:
            offer_price = normal_price

        description = html_to_markdown(str(description_tag))
        picture_urls = [x.find('a')['href'] for x in soup.findAll('div', 'woocommerce-product-gallery__image')]

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
            sku=key,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
