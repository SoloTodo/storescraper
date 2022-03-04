import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, COMPUTER_CASE, HEADPHONES, \
    MONITOR, KEYBOARD, POWER_SUPPLY, GAMING_CHAIR, RAM, VIDEO_CARD, CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class GeneracionGamers(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            COMPUTER_CASE,
            HEADPHONES,
            KEYBOARD,
            MONITOR,
            POWER_SUPPLY,
            GAMING_CHAIR,
            RAM,
            VIDEO_CARD,
            CPU_COOLER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['mouse', MOUSE],
            ['gabinetes', COMPUTER_CASE],
            ['audifonos', HEADPHONES],
            ['teclados', KEYBOARD],
            ['monitores', MONITOR],
            ['fuente-de-poder', POWER_SUPPLY],
            ['sillas-gamers', GAMING_CHAIR],
            ['componentes', RAM],
            ['tarjetas-graficas', VIDEO_CARD],
            ['refrigeracion', CPU_COOLER],
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
                url_webpage = 'https://generacion-gamers.cl/categoria-prod' \
                              'ucto/{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('ul', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('li'):
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
        product_container = soup.find('script',
                                      {'type': 'application/ld+json'})
        if product_container:
            product_container = json.loads(product_container.text)
        else:
            return []

        name = product_container['name']
        sku = str(product_container['sku'])
        description = product_container['description']
        offer_price = Decimal(product_container['offers'][0]['price'])
        normal_price = (offer_price * Decimal('1.035')).quantize(0)
        picture_urls = [product_container['image']]

        if product_container['offers'][0]['availability'].split('/')[-1] == \
                'OutOfStock':
            stock = 0
        elif 'PREVENTA' in description.upper():
            stock = 0
        else:
            stock = -1

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
