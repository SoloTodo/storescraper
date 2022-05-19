import json
import logging
import re
from decimal import Decimal

import demjson
from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, KEYBOARD, HEADPHONES, \
    MONITOR, MOUSE, COMPUTER_CASE, MOTHERBOARD, POWER_SUPPLY, CPU_COOLER, \
    VIDEO_CARD, RAM, STEREO_SYSTEM, GAMING_DESK, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Sepuls(Store):
    @classmethod
    def categories(cls):
        return [
            POWER_SUPPLY,
            GAMING_CHAIR,
            KEYBOARD,
            HEADPHONES,
            MONITOR,
            MOUSE,
            COMPUTER_CASE,
            MOTHERBOARD,
            CPU_COOLER,
            VIDEO_CARD,
            RAM,
            GAMING_DESK,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
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
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

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
        key_tag = soup.find('form', 'product-form')
        key = re.search(r'(\d+)', key_tag['id']).groups()[0]
        product_data = demjson.decode(
            soup.find('script', {'type': 'application/ld+json'})
                .text)
        name = product_data['name']
        sku = product_data.get('sku', key)
        normal_price = Decimal(product_data['offers']['price'])

        offer_price_label_tag = soup.find('td', text='Precio Transferencia')
        if offer_price_label_tag:
            offer_price_tag = offer_price_label_tag.parent.findAll('td')[1]
            if offer_price_tag.text.strip():
                offer_price = Decimal(
                    offer_price_tag.text.strip().replace('.', ''))
                if offer_price > normal_price:
                    offer_price = normal_price
            else:
                offer_price = normal_price
        else:
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
