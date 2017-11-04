import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Terabyte(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'SolidStateDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['hardware/hard-disk/hd-sata-iii', 'StorageDrive'],
            ['hardware/hard-disk/ssd', 'SolidStateDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.terabyteshop.com.br/{}' \
                           ''.format(category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            containers = soup.findAll('div', 'pbox')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = 'https://www.terabyteshop.com.br' + \
                              container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        sku = soup.find('input', {'id': 'idproduto'})['value'].strip()

        pricing_json = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        name = pricing_json['name']
        part_number = pricing_json['mpn']
        offer_price = Decimal(pricing_json['offers']['price'])

        if pricing_json['offers']['availability'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        normal_price = (offer_price / Decimal('0.85')).quantize(
            Decimal('0.01'))

        description = html_to_markdown(str(soup.find('div', 'tecnicas')),
                                       'https://www.terabyteshop.com.br')

        picture_urls = [tag['data-zoom-image'] for tag in
                        soup.findAll('a', 'thumbnail')]

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
            'BRL',
            sku=sku,
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
