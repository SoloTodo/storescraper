import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import NOTEBOOK, ALL_IN_ONE, TABLET, \
    STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, SOLID_STATE_DRIVE, MEMORY_CARD, \
    USB_FLASH_DRIVE, PROCESSOR, COMPUTER_CASE, POWER_SUPPLY, MOTHERBOARD, \
    RAM, VIDEO_CARD, MOUSE, PRINTER, HEADPHONES, STEREO_SYSTEM, UPS, MONITOR, \
    KEYBOARD_MOUSE_COMBO, KEYBOARD


class Cintegral(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            ALL_IN_ONE,
            TABLET,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            PROCESSOR,
            COMPUTER_CASE,
            POWER_SUPPLY,
            MOTHERBOARD,
            RAM,
            VIDEO_CARD,
            MOUSE,
            PRINTER,
            HEADPHONES,
            STEREO_SYSTEM,
            UPS,
            MONITOR,
            KEYBOARD_MOUSE_COMBO,
            KEYBOARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://www.cintegral.cl/index.php?' \
                   'id_category={}&controller=category&page={}'

        url_extensions = [
            ['4', NOTEBOOK],
            ['5', ALL_IN_ONE],
            ['59', STORAGE_DRIVE],
            ['60', EXTERNAL_STORAGE_DRIVE],
            ['61', SOLID_STATE_DRIVE],
            ['62', MEMORY_CARD],
            ['63', USB_FLASH_DRIVE],
            ['13', PROCESSOR],
            ['14', COMPUTER_CASE],
            ['15', POWER_SUPPLY],
            ['16', MOTHERBOARD],
            ['17', RAM],
            ['18', VIDEO_CARD],
            ['22', KEYBOARD_MOUSE_COMBO],
            ['23', MOUSE],
            ['21', KEYBOARD],
            ['29', PRINTER],
            ['48', HEADPHONES],
            ['49', STEREO_SYSTEM],
            ['46', MONITOR],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + url_extension)

                url = url_base.format(url_extension, page)
                source = session.get(url, verify=False).text
                soup = BeautifulSoup(source, 'html.parser')

                products = soup.find('div', 'products row')

                if not products:
                    if page == 1:
                        logging.warning('Empty category: ' + url)
                    break

                containers = soup.find('div', 'products row') \
                    .findAll('a', 'product-thumbnail')

                for product_link in containers:
                    product_url = product_link['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url, verify=False).text
        soup = BeautifulSoup(page_source, 'html.parser')
        name = soup.find('h1', 'product-detail-title').text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value']

        part_number = None
        part_number_container = soup.find('span', {'itemprop': 'sku'})
        if part_number_container:
            part_number = part_number_container.text.strip()

        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

        add_to_cart_button = soup.find('button', 'add-to-cart')

        if 'disabled' in add_to_cart_button.attrs:
            stock = 0
        else:
            stock = -1

        price = Decimal(soup.find('div', 'current-price')
                        .find('span', {'itemprop': 'price'})['content'])

        pictures = soup.find('ul', 'product-images').findAll('img')
        picture_urls = [p['data-image-large-src'] for p in pictures]

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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
