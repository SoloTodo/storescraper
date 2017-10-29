import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13


class Pichau(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'SolidStateDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['hardware/hard-disk-e-ssd', 'StorageDrive'],
            ['hardware/ssd', 'SolidStateDrive'],
            ['perifericos/armazenamento', 'MemoryCard'],
            ['perifericos/pendrives', 'UsbFlashDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.pichau.com.br/{}?limit=48&p={}' \
                               ''.format(category_path, page)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                containers = soup.findAll('li', 'item')

                for container in containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                if not soup.find('a', 'bt-next'):
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        pricing_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)[0]

        name = pricing_data['name']
        sku = pricing_data['sku']
        description = pricing_data.get('description')

        if 'gtin13' in pricing_data:
            ean = pricing_data['gtin13'].strip()
            if len(ean) == 12:
                ean = '0' + ean
            if not check_ean13(ean):
                ean = None
        else:
            ean = None

        offer_price = Decimal(pricing_data['offers']['price'])

        if pricing_data['offers']['availability'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        normal_price = Decimal(
            soup.find('li', 'regular-price').text.replace('R$', '').replace(
                '.', '').replace(',', '.'))

        pictures_container = soup.find('ul', 'slides')
        if pictures_container:
            picture_urls = [tag['href'] for tag in
                            pictures_container.findAll('a')]
        else:
            picture_urls = None

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
            ean=ean,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
