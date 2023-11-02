import json
import logging
import re
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import (STEREO_SYSTEM, VIDEO_GAME_CONSOLE, MONITOR,
                                     HEADPHONES, WEARABLE)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class TecnoPro(StoreWithUrlExtensions):
    url_extensions = [
        ['audifonos', HEADPHONES],
        ['consolas-y-videojuegos', VIDEO_GAME_CONSOLE],
        ['computacion', HEADPHONES],
        ['electronica-audio-y-video', HEADPHONES],
        ['parlantes', STEREO_SYSTEM],
        ['apple', HEADPHONES],
        ['celulares-y-telefonia', WEARABLE],
        ['monitores', MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://tecnopro.cl/collections/{}/'.format(url_extension)

            if page > 1:
                url_webpage += 'page/{}/'.format(page)

            print(url_webpage)
            response = session.get(url_webpage)

            if response.url != url_webpage:
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('div', 'product-grid-item')

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
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)

        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[-1]
        name = soup.find('h1', 'product_title').text.strip()
        sku = product_data.get('sku', None)
        description = product_data.get('description', None)
        stock_tag = soup.find('p', 'stock')
        stock_match = re.match(r'(\d+)', stock_tag.text)
        if stock_match:
            stock = int(stock_match.groups()[0])
        else:
            stock = 0

        normal_price = Decimal(product_data['offers']['price'])
        offer_price = (normal_price * Decimal('0.98')).quantize(0)

        picture_urls = [tag.find('a')['href'] for tag in
                        soup.findAll('div', 'product-image-wrap')
                        if validators.url(tag.find('a')['href'])
                        ]

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
            picture_urls=picture_urls,
            description=description
        )

        return [p]
