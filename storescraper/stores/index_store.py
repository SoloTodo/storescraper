from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import EXTERNAL_STORAGE_DRIVE, HEADPHONES, \
    MOUSE, POWER_SUPPLY, RAM, SOLID_STATE_DRIVE, STORAGE_DRIVE, USB_FLASH_DRIVE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class IndexStore(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            RAM,
            POWER_SUPPLY,
            MOUSE,
            HEADPHONES,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['discos-duros', STORAGE_DRIVE],
            ['discos-ssd', SOLID_STATE_DRIVE],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['pendrive-y-micro-sd', USB_FLASH_DRIVE],
            ['memorias-ram', RAM],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['accesorios-perifericos', MOUSE],
            ['audio', HEADPHONES],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.indexstore.cl/collections/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find(
                        'a', 'product-item__image-wrapper')['href']
                    product_urls.append(
                        'https://www.indexstore.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(soup.find(
            'script', {
                'type': 'application/json',
                'data-product-json': True}).text)['product']

        if json_data['description']:
            description = html_to_markdown(json_data['description'])
        else:
            description = None
        picture_urls = [m['src'] for m in json_data['media']]

        products = []
        for variant in json_data['variants']:
            key = str(variant['id'])
            sku = variant['sku']
            name = variant['name']
            price = Decimal(str(variant['price'])) / Decimal(100)
            if variant['available']:
                stock = -1
            else:
                stock = 0

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
                sku=sku,
                part_number=sku,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)
        return products
