import logging
import re
from decimal import Decimal

import pyjson5
from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, KEYBOARD, HEADPHONES, \
    MONITOR, MOUSE, COMPUTER_CASE, MOTHERBOARD, POWER_SUPPLY, CPU_COOLER, \
    VIDEO_CARD, RAM, STEREO_SYSTEM, GAMING_DESK, MICROPHONE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Sepuls(StoreWithUrlExtensions):
    url_extensions = [
        ['sillas-gamer', GAMING_CHAIR],
        ['audifonos-gamer', HEADPHONES],
        ['teclado-gamer', KEYBOARD],
        ['mouse-gamer', MOUSE],
        ['monitor-gamer', MONITOR],
        ['componentes-para-pc/tarjeta-de-video', VIDEO_CARD],
        ['componentes-para-pc/refrigeracion', CPU_COOLER],
        ['componentes-para-pc/gabinete-gamer', COMPUTER_CASE],
        ['componentes-para-pc/memoria-ram', RAM],
        ['accesorios/placa-madre', MOTHERBOARD],
        ['componentes-para-pc/fuente-de-poder', POWER_SUPPLY],
        ['accesorios/parlantes', STEREO_SYSTEM],
        ['accesorios/escritorios', GAMING_DESK],
        ['streaming/microfonos', MICROPHONE]
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://www.sepuls.cl/{}/?page={}' \
                .format(url_extension, page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div', 'product-block')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append('https://sepuls.cl' + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_data = pyjson5.decode(
            soup.find('script', {'type': 'application/ld+json'})
            .text)

        if not Decimal(product_data['offers']['price']):
            return []

        key_tag = soup.find('form', 'product-form')
        key = re.search(r'(\d+)', key_tag['id']).groups()[0]
        name = product_data['name']
        sku = product_data.get('sku', key)

        price_containers = soup.find(
            'div', 'form-group').findAll('span', 'product-form-price')
        assert len(price_containers) == 2

        offer_price = Decimal(remove_words(price_containers[0].text)
                              .replace(' CLP', ''))
        normal_price = Decimal(remove_words(price_containers[1].text)
                               .replace(' CLP', ''))

        if offer_price > normal_price:
            offer_price = normal_price

        stock_tag = soup.find('span', 'product-form-stock')
        if stock_tag:
            stock = int(stock_tag.text)
        else:
            stock = 0

        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div', 'main-product-image').findAll(
                            'img', 'img-fluid')]
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
