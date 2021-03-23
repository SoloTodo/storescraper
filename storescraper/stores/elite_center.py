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
    GAMING_CHAIR, NOTEBOOK
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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes-pc/procesadores', PROCESSOR],
            ['componentes-pc/placas-madres', MOTHERBOARD],
            ['componentes-pc/tarjetas-de-video', VIDEO_CARD],
            ['componentes-pc/memorias-ram/', RAM],
            ['componentes-pc/fuente-de-poder', POWER_SUPPLY],
            ['componentes-pc/refrigeracion', CPU_COOLER],
            ['componentes-pc/gabinetes', COMPUTER_CASE],
            ['accesorios-gamer/audifonos', HEADPHONES],
            ['accesorios-gamer/teclados', KEYBOARD],
            ['accesorios-gamer/mouse', MOUSE],
            ['accesorios-gamer/parlantes', STEREO_SYSTEM],
            ['almacenamiento/disco-duro-pcs', STORAGE_DRIVE],
            ['almacenamiento/disco-estado-solido', SOLID_STATE_DRIVE],
            ['monitores', MONITOR],
            ['sillas-gamer', GAMING_CHAIR],
            ['notebooks', NOTEBOOK],
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'

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
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html5lib')
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
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-title').text
        if not soup.find('button', 'single_add_to_cart_button'):
            return []
        sku = soup.find('button', 'single_add_to_cart_button')['value']

        part_number_container = soup.find('span', {'id': '_sku'})
        if part_number_container:
            part_number = part_number_container.text.strip()
        else:
            part_number = None

        if soup.find('p', 'stock'):
            stock = int(
                re.search(r'(\d+)', soup.find('p', 'stock').text).groups()[0])
        else:
            stock = -1
        normal_price = Decimal(
            remove_words(soup.find('p', 'precio-webpay').text))
        if soup.find('p', 'precio-oferta'):
            offer_price = Decimal(soup.find('p', 'precio-oferta').text.
                                  split('$')[1].replace('.', ''))
        else:
            offer_price = Decimal(
                remove_words(soup.find('p', 'precio-normal').text))
        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div', 'product-gallery').findAll('img')
                        if validators.url(tag['src'])
                        ]

        description = html_to_markdown(str(soup.find('div', 'tabbed-content')))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls,
            description=description

        )
        return [p]
