import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import MONITOR, KEYBOARD
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
            'SolidStateDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Ram',
            MONITOR,
            KEYBOARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['lacie-chile/discos-externos', 'ExternalStorageDrive'],
            ['lacie-chile/discos-portatiles', 'ExternalStorageDrive'],
            ['lacie-chile/discos-thunderbolt', 'ExternalStorageDrive'],
            ['discos-duros-externos',
             'ExternalStorageDrive'],
            ['discos-duros-portatiles', 'ExternalStorageDrive'],
            ['monitores-lcd-tv-led', MONITOR],
            ['teclados-mac', KEYBOARD],
            ['discos-duros-notebook-sata-2.5', 'SolidStateDrive'],
            ['discos-duros-sata-3.5', 'SolidStateDrive'],
            ['discos-duros-ssd-sata-2.5', 'SolidStateDrive'],
            ['SSD-M-2-PCie-NVMe', 'SolidStateDrive'],
            ['SSD-M2-SATA', 'SolidStateDrive'],
            ['SSD-mSATA', 'SolidStateDrive'],
            ['memorias-ram', 'Ram'],
            ['Tarjetas-Expansion-Flashdrive-SDCard-y-SSD-para-Apple-Mac',
             'MemoryCard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.globalmac.cl/' + category_path
            print(category_url)
            soup = BeautifulSoup(session.get(category_url).text,
                                 'html.parser')

            items = soup.findAll('div', 'product-layout')

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
        sku = soup.find('input', {'name': 'product_id'})['value']

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))
        pictures_container = soup.find('ul', 'thumbnails')

        if pictures_container:
            picture_urls = [tag['href'] for tag in pictures_container.findAll(
                'a', 'thumbnail') if tag['href']]
        else:
            picture_urls = None

        add_to_cart_button = soup.find('button', {'id': 'button-cart'})
        if 'btn-primary' in add_to_cart_button.attrs.get('class', []):
            stock = -1
        else:
            stock = 0

        price_text = soup.findAll('h2')[-1].text.replace('.', '')

        normal_price = re.search(r'Webpay: \$(\d+)', price_text)
        normal_price = Decimal(normal_price.groups()[0])

        offer_price = re.search(r'Transferencia: \$(\d+)', price_text)
        offer_price = Decimal(offer_price.groups()[0])

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
            'CLP',
            sku=sku,
            part_number=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
