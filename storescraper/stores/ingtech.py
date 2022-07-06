import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import STORAGE_DRIVE, POWER_SUPPLY, \
    COMPUTER_CASE, RAM, MONITOR, MOUSE, MOTHERBOARD, PROCESSOR, CPU_COOLER, \
    VIDEO_CARD, HEADPHONES, GAMING_CHAIR, NOTEBOOK, TABLET
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Ingtech(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            HEADPHONES,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOUSE,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_CARD,
            NOTEBOOK,
            GAMING_CHAIR,
            TABLET,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento', STORAGE_DRIVE],
            ['audio', HEADPHONES],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['memorias-ram', RAM],
            ['monitores', MONITOR],
            ['mouse-y-teclado', MOUSE],
            ['notebook', NOTEBOOK],
            ['placas-madres', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['refrigeracion', CPU_COOLER],
            ['setup-gamer', GAMING_CHAIR],
            ['tarjetas-graficas', VIDEO_CARD],
            ['tablet', TABLET],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overlfow: ' + url_extension)

                url_webpage = 'https://store.ingtech.cl/categoria-producto/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-grid-item')

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
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')
        json_data = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        product_data = json_data['@graph'][1]
        picture_urls = [tag.find('a')['href']
                        for tag in soup.findAll(
                'figure', 'woocommerce-product-gallery__image')]
        sku = str(product_data['sku'])
        name = product_data['name']
        description = product_data['description']

        prices_tag = soup.find('p', 'price')
        normal_price = Decimal(remove_words(prices_tag.find(
            'bdi').text.split('$')[1]))
        if prices_tag.find('span', 'pro_price_extra_info'):
            if '$' in prices_tag.find('span', 'pro_price_extra_info').text:
                offer_price = Decimal(remove_words(prices_tag.find(
                    'span', 'pro_price_extra_info').text.split('$')[1]))
            else:
                offer_price = Decimal(
                    prices_tag.find('span', 'pro_price_extra_info').text.split(

                    )[-1].replace('.', ''))
        else:
            offer_price = normal_price

        stock_tag = soup.find('input', {'name': 'quantity'})
        if stock_tag:
            if 'max' in stock_tag.attrs and stock_tag['max'] != "":
                stock = int(stock_tag['max'])
            elif 'max' in stock_tag.attrs:
                stock = -1
            else:
                stock = 1
        else:
            stock = 0

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
            picture_urls=picture_urls,
            description=description
        )
        return [p]
