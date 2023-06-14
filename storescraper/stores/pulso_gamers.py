from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import COMPUTER_CASE, GAMING_CHAIR, HEADPHONES, \
    KEYBOARD, MOUSE, POWER_SUPPLY
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class PulsoGamers(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE, GAMING_CHAIR, HEADPHONES, KEYBOARD, MOUSE,
            POWER_SUPPLY
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['torres', COMPUTER_CASE],
            ['mouse', MOUSE],
            ['sillas-gamer', GAMING_CHAIR],
            ['teclados', KEYBOARD],
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
                url_webpage = 'https://pulsogamers.cl/collections/' \
                              '{}?page={}'.format(
                                  url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage, timeout=60)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'card__information')

                if not product_containers:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = 'https://pulsogamers.cl' + \
                                  container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        key = soup.find('input', {'type': 'hidden', 'name': 'id'})['value']
        product_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[1].text)
        name = product_data['name']
        description = product_data['description']
        picture_urls = product_data['image']
        offer = product_data['offers'][0]

        if offer['availability'] == 'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        price = Decimal(offer['price'])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'CLP',
            sku=key,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
