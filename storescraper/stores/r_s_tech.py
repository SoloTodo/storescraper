import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD, MOTHERBOARD, POWER_SUPPLY, \
    RAM, PROCESSOR, CPU_COOLER, NOTEBOOK, VIDEO_GAME_CONSOLE, \
    STORAGE_DRIVE, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class RSTech(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_CARD,
            MOTHERBOARD,
            POWER_SUPPLY,
            RAM,
            PROCESSOR,
            CPU_COOLER,
            NOTEBOOK,
            VIDEO_GAME_CONSOLE,
            STORAGE_DRIVE,
            MOUSE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['consolas-y-videojuegos', VIDEO_GAME_CONSOLE],
            ['disco-duro-y-almacenamiento', STORAGE_DRIVE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['memoria-ram', RAM],
            ['notebook-gamer', NOTEBOOK],
            ['audifonos-y-perifericos', MOUSE],
            ['placa-madre-motherboard', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['refrigeracion', CPU_COOLER],
            ['tarjetas-de-video', VIDEO_CARD],
            # ['monitores', MONITOR],
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

                url_webpage = 'https://rstech.cl/categoria-producto/' \
                              'productos/{}/page/{}/'.format(url_extension,
                                                             page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_container = soup.findAll('div', 'product-small')

                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_container:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-title').text

        bundle_tag = soup.find('span', 'bundled_product_title_inner')
        if bundle_tag:
            name += ' + ' + bundle_tag.text.strip()

        sku_tag = soup.find('span', 'sku')

        if sku_tag:
            sku = sku_tag.text.strip()
        else:
            sku = None

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock in-stock'):
            stock = -1
        else:
            stock = 0
        if soup.find('p', 'price').find('ins'):
            offer_price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text.strip()))
        else:
            offer_price = Decimal(
                remove_words(soup.find('p', 'price').text.strip()))

        normal_price = (offer_price * Decimal('1.03')).quantize(0)

        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'product-gallery').findAll('img')
                        if validators.url(tag['src'])
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
        )
        return [p]
