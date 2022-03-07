import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, STORAGE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, SOLID_STATE_DRIVE, HEADPHONES, STEREO_SYSTEM, \
    KEYBOARD, COMPUTER_CASE, CPU_COOLER, POWER_SUPPLY, RAM, MEMORY_CARD, \
    USB_FLASH_DRIVE, GAMING_CHAIR, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class PcInfinity(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            HEADPHONES,
            STEREO_SYSTEM,
            KEYBOARD,
            COMPUTER_CASE,
            CPU_COOLER,
            POWER_SUPPLY,
            RAM,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            GAMING_CHAIR,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['18-discos-duros', STORAGE_DRIVE],
            ['22-discos-externos', EXTERNAL_STORAGE_DRIVE],
            ['19-discos-solidos', SOLID_STATE_DRIVE],
            ['25-audifonos-gamer', HEADPHONES],
            ['24-audifonos', HEADPHONES],
            ['23-parlantes', STEREO_SYSTEM],
            ['13-teclados', KEYBOARD],
            ['14-mouse', MOUSE],
            ['16-gabinetes', COMPUTER_CASE],
            ['78-ventiladores-para-cpu', CPU_COOLER],
            ['51-fuentes-de-poder', POWER_SUPPLY],
            ['60-memorias-pc', RAM],
            ['61-memorias-notebook', RAM],
            ['62-memorias-flash', MEMORY_CARD],
            ['64-pendrives', USB_FLASH_DRIVE],
            ['82-sillas-gamer', GAMING_CHAIR],
            ['49-ventiladores-para-gabinetes', CASE_FAN],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://www.pc-infinity.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.find('div', 'products row')

                if not product_containers:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break
                for container in product_containers.findAll(
                        'article', 'product-miniature'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_data = soup.find('div', 'row product_container')
        name = product_data.find('h1', 'product_name').text
        key = product_data.find('input', {'name': 'id_product'})['value']
        sku = soup.find('span', {'itemprop': 'sku'}).text.strip()
        if product_data.find('span', {'id': 'product-availability'})\
                .text.strip() == '':
            stock = -1
        else:
            stock = 0
        price = Decimal(product_data.find('span', 'price').text.replace(
            '$\xa0', '').replace('.', ''))
        picture_urls = [tag['src'] for tag in
                        product_data.find('ul', 'product-images')
                        .findAll('img')]
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
            picture_urls=picture_urls,

        )
        return [p]
