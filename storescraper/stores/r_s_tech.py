import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD, MOTHERBOARD, POWER_SUPPLY, \
    RAM, PROCESSOR, CPU_COOLER, NOTEBOOK, MONITOR, VIDEO_GAME_CONSOLE, \
    STORAGE_DRIVE
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
            MONITOR,
            VIDEO_GAME_CONSOLE,
            STORAGE_DRIVE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accesorios-y-componentes/tarjetas-de-video', VIDEO_CARD],
            ['accesorios-y-componentes/placa-madre-motherboard', MOTHERBOARD],
            ['accesorios-y-componentes/fuentes-de-poder', POWER_SUPPLY],
            ['accesorios-y-componentes/memoria-ram', RAM],
            ['accesorios-y-componentes/procesadores', PROCESSOR],
            ['accesorios-y-componentes/refrigeracion', CPU_COOLER],
            ['sin-categoria/notebook-gamer', NOTEBOOK],
            ['monitores', MONITOR],
            ['consolas-y-videojuegos', VIDEO_GAME_CONSOLE],
            ['accesorios-y-componentes/disco-duro-y-almacenamiento',
             STORAGE_DRIVE],
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

                url_webpage = 'https://rstech.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
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
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock in-stock'):
            stock = -1
        else:
            stock = 0
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text.strip()))
        else:
            price = Decimal(
                remove_words(soup.find('p', 'price').text.strip()))

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
            sku,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
