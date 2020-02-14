import html
import json
import re
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown


class MercadolibreChile(Store):
    @classmethod
    def categories(cls):
        raise NotImplementedError('Subclasses must implement this')

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        raise NotImplementedError('Subclasses must implement this')

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = requests.Session()
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('meta', {'name': 'twitter:title'})['content'].strip()
        description = html_to_markdown(
            str(soup.find('section', 'item-description')))
        pictures_data = json.loads(html.unescape(
            soup.find('div', 'gallery-content')['data-full-images']))
        picture_urls = [e['src'] for e in pictures_data]

        pricing_str = re.search(r'dataLayer = ([\S\s]+?);',
                                page_source).groups()[0]
        pricing_data = json.loads(pricing_str)[0]

        sku = pricing_data['itemId']
        price = Decimal(pricing_data['localItemPrice'])
        stock = pricing_data['availableStock']

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
