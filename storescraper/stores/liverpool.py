import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Liverpool(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)

        base_url = 'https://www.liverpool.com.mx'

        category_paths = [
            ['discos-duros/cat670064', 'ExternalStorageDrive'],
            ['otros-accesorios/cat170402', 'MemoryCard'],
            ['otros-accesorios/cat4450184', 'MemoryCard'],
            ['memorias-usb/cat670073', 'UsbFlashDrive'],
        ]

        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = '{}/tienda/{}'.format(base_url, category_path)
            print(category_url)

            response = session.get(category_url)

            if response.url != category_url:
                product_urls.append(response.url)
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            link_containers = soup.findAll('a', 'product-name')

            if not link_containers:
                raise Exception('Empty category: ' + category_url)

            for link_container in link_containers:
                product_url = base_url + link_container['href'].split('?')[0]
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', {'id': 'productName'}).find('h1').text.strip()
        sku = soup.find('input', {'id': 'prodId'})['value'].strip()

        price_container = soup.find('input', {'id': 'requiredsaleprice'})
        price = price_container['value']
        price = Decimal(price)

        description = html_to_markdown(
            str(soup.find('section', {'id': 'description'})))

        pictures_json = json.loads(
            soup.find('input', {'id': 'jsonImageMap'})['value'])

        picture_urls = []

        for suffix in ['th', 'lg', 'sm']:
            key = sku + '_' + suffix
            if key in pictures_json:
                picture_urls.append(pictures_json[key])
                break

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'MXN',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
