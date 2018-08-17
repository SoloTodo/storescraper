import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class MercadoLibreArgentina(Store):
    store_id = ''

    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'SolidStateDrive',
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        offset = 1
        product_urls = []

        if category != 'StorageDrive':
            return []

        while True:
            category_url = 'https://listado.mercadolibre.com.ar/_Desde_{}{}' \
                           ''.format(offset, cls.store_id)
            print(category_url)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            product_containers = soup.findAll('li', 'results-item')

            if not product_containers:
                if offset == 1:
                    raise Exception('Empty store: {}'.format(category_url))
                break

            for container in product_containers:
                product_urls.append(container.find('a')['href'])

            offset += 48

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'item-title__primary').text.strip()
        sku = soup.find('input', {'name': 'item_id'})['value'].strip()
        price = Decimal(soup.find('span', 'price-tag').find(
            'span', 'price-tag-symbol')['content'])

        sections = ['vip-section-specs', 'item-description']

        description = ''

        for section in sections:
            description += html_to_markdown(
                str(soup.find('section', section))) + '\n\n'

        pictures_data = json.loads(
            soup.find('div', 'gallery-content')['data-full-images'])
        picture_urls = [e['src'] for e in pictures_data]

        return [Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )]
