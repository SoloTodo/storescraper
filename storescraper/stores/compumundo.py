import json

import re

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Compumundo(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'StorageDrive',
            'ExternalStorageDrive',
            'SolidStateDrive'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.compumundo.com.ar'

        category_paths = [
            ['discos-rigidos/4721', 'StorageDrive'],
            ['pendrive/4713', 'UsbFlashDrive'],
            ['tarjeta-de-memoria-celulares/3761', 'MemoryCard'],
            ['tarjeta-microsd-tablets/3777', 'MemoryCard'],
            # ['disco-rigido-externo/4716', 'ExternalStorageDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = '{}/productos/{}'.format(base_url, category_path)
            page_source = session.get(category_url).text

            soup = BeautifulSoup(page_source, 'html5lib')

            product_cells = soup.findAll('div', 'itemBox')

            if not product_cells:
                raise Exception('Empty category: ' + category_url)

            for cell in product_cells:
                product_url = base_url + cell.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        sku = soup.find('body')['data-product-id']

        pricing_data = soup.find('script', {'type': 'application/ld+json'})
        pricing_json = json.loads(pricing_data.text)

        name = pricing_json['name']
        price = Decimal(pricing_json['offers']['price'])
        currency = pricing_json['offers']['priceCurrency']

        if pricing_json['offers']['availability'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        description = html_to_markdown(str(soup.find('div', 'gb-tech-spec')))

        picture_urls = []

        for container in soup.findAll('li', 'gb-js-popup-thumbnail'):
            image_url = container.find('a')['href']
            if 'http' in image_url:
                continue
            image_url = 'https:' + image_url
            image_url = image_url.replace('_1000', '')
            picture_urls.append(image_url)

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
            currency,
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
