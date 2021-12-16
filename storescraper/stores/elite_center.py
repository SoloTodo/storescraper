import logging
import re
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import HEADPHONES, SOLID_STATE_DRIVE, \
    MOUSE, KEYBOARD, CPU_COOLER, COMPUTER_CASE, \
    POWER_SUPPLY, RAM, MONITOR, MOTHERBOARD, \
    PROCESSOR, VIDEO_CARD, STEREO_SYSTEM, STORAGE_DRIVE, VIDEO_GAME_CONSOLE, \
    GAMING_CHAIR, NOTEBOOK, EXTERNAL_STORAGE_DRIVE
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class EliteCenter(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            STEREO_SYSTEM,
            STORAGE_DRIVE,
            MOUSE,
            KEYBOARD,
            SOLID_STATE_DRIVE,
            CPU_COOLER,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            VIDEO_GAME_CONSOLE,
            GAMING_CHAIR,
            NOTEBOOK,
            EXTERNAL_STORAGE_DRIVE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes-pc/disco-externo', EXTERNAL_STORAGE_DRIVE],
            ['componentes-pc/procesadores', PROCESSOR],
            ['componentes-pc/placas-madres', MOTHERBOARD],
            ['componentes-pc/tarjetas-de-video', VIDEO_CARD],
            ['componentes-pc/memorias-ram', RAM],
            ['componentes-pc/fuente-de-poder', POWER_SUPPLY],
            ['componentes-pc/refrigeracion', CPU_COOLER],
            ['componentes-pc/gabinetes', COMPUTER_CASE],
            ['accesorios/audifonos', HEADPHONES],
            ['accesorios/teclados', KEYBOARD],
            ['accesorios/mouse', MOUSE],
            ['accesorios/parlantes', STEREO_SYSTEM],
            ['almacenamiento/disco-duro-pc-hdd', STORAGE_DRIVE],
            ['almacenamiento/disco-estado-solido-ssd', SOLID_STATE_DRIVE],
            ['almacenamiento/disco-externo', EXTERNAL_STORAGE_DRIVE],
            ['monitores', MONITOR],
            ['sillas-gamer', GAMING_CHAIR],
            ['notebooks', NOTEBOOK],
            ['consolas', VIDEO_GAME_CONSOLE],
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

                url_webpage = 'https://elitecenter.cl/product-category/{}/' \
                              'page/{}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)

                if response.status_code == 404:
                    if page == 1:
                        raise Exception('Invalid category: ' + url_extension)
                    break

                data = response.text
                soup = BeautifulSoup(data, 'html5lib')
                product_containers = soup.findAll('div', 'product-grid-item')

                for container in product_containers:
                    if container.find('span', 'out-of-stock'):
                        continue
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

        if soup.find('input', 'current_product_id'):
            key = soup.find('input', 'current_product_id')['value']
        else:
            key = soup.find('button', 'single_add_to_cart_button')['value']

        sku_tag = soup.find('div', {'data-id': '6897d6e'})
        sku = sku_tag.text.split('SKU: ')[1].strip()

        if soup.find('button', 'stock_alert_button'):
            stock = 0
        else:
            stock_tag = soup.find('p', 'stock')
            if stock_tag:
                stock = int(re.search(r'(\d+)', stock_tag.text).groups()[0])
            else:
                stock = -1

        normal_price = Decimal(
            remove_words(soup.find('p', 'precio-webpay').text))
        if soup.find('p', 'precio-oferta'):
            offer_price = Decimal(soup.find('p', 'precio-oferta').text.
                                  split('$')[1].replace('.', ''))
        else:
            price_text = soup.find('p', 'precio-normal').text.strip()
            if price_text == '$':
                return []
            offer_price = Decimal(
                remove_words(soup.find('p', 'precio-normal').text))
        picture_urls = [tag['href'].split('?')[0] for tag in
                        soup.find(
                            'figure', 'woocommerce-product-gallery__wrapper')
                        .findAll('a')
                        if validators.url(tag['href'])
                        ]

        description = soup.find('meta', {'name': 'description'})['content']

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
            part_number=sku,
            picture_urls=picture_urls,
            description=description

        )
        return [p]
