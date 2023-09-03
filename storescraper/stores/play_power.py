import re
from decimal import Decimal
import json
import logging
import validators

from bs4 import BeautifulSoup

from storescraper.categories import MONITOR
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class PlayPower(StoreWithUrlExtensions):
    url_extensions = [
        ['all', MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://playpower.cl/collections/{}?page={}'.format(
                url_extension, page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll(
                'li', 'grid__item')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_path = container.find('a')['href']
                product_urls.append('https://playpower.cl' + product_path)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)
        name = product_data['name']
        description = product_data['description']
        offer = product_data['offers'][0]
        key = offer['url'].split('?variant=')[1].strip()
        price = Decimal(offer['price']).quantize(0)

        if offer['availability'] == 'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        picture_urls = ['https:' + x['src'] for x in
                        soup.find('div', 'product-media-modal__content'
                                  ).findAll('img')]

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
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
