import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import EXTERNAL_STORAGE_DRIVE, MEMORY_CARD, \
    MONITOR, KEYBOARD, RAM, SOLID_STATE_DRIVE, STORAGE_DRIVE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class GlobalMac(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'StorageDrive',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'Ram',
            MONITOR,
            KEYBOARD,
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MEMORY_CARD,
            RAM,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # ['lacie-chile/discos-externos', 'ExternalStorageDrive'],
            # ['lacie-chile/discos-portatiles', 'ExternalStorageDrive'],
            # ['lacie-chile/discos-thunderbolt', 'ExternalStorageDrive'],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['discos-portatiles', EXTERNAL_STORAGE_DRIVE],
            ['monitores-lcd-tv-led', MONITOR],
            ['teclados-mac', KEYBOARD],
            # ['discos-duros-notebook-sata-2.5', SOLID_STATE_DRIVE],
            ['discos-duros-sata-3_5', STORAGE_DRIVE],
            ['discos-duros-ssd-sata-2_5', STORAGE_DRIVE],
            ['SSD-M-2-PCie-NVMe', SOLID_STATE_DRIVE],
            ['SSD-M2-SATA', SOLID_STATE_DRIVE],
            ['SSD-mSATA', SOLID_STATE_DRIVE],
            ['memorias-ram', RAM],
            ['tarjetas-de-expansion-para-mac', MEMORY_CARD],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.globalmac.cl/index.php?' + \
                'category_rewrite=' + category_path + '&controller=category'
            print(category_url)
            soup = BeautifulSoup(session.get(category_url).text,
                                 'html.parser')

            items = soup.findAll('article', 'product-miniature')

            for item in items:
                product_urls.append(item.find('a')['href'])

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['Accept-Encoding'] = 'deflate'
        response = session.get(url)

        if response.status_code == 500:
            return []

        soup = BeautifulSoup(response.text,
                             'html.parser')

        name = soup.find('title').text.strip()
        key = soup.find('input', {'id': 'product_page_product_id'})['value']
        sku = soup.find('span', {'itemprop': 'sku'}).text

        description = html_to_markdown(
            str(soup.find('div', {'id': 'product-description-short-260'})))

        pictures_container = soup.find('div', 'js-qv-mask')
        if pictures_container:
            picture_urls = [tag['data-image-large-src']
                            for tag in pictures_container.findAll(
                                'img') if tag['data-image-large-src']]
        else:
            picture_urls = None

        stock = 0
        stock_number = soup.find(
            'div', 'product-quantities').find('span')['data-stock']
        if stock_number:
            stock = int(stock_number)

        price = Decimal(
            soup.find('div', 'current-price').find('span')['content'])

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
