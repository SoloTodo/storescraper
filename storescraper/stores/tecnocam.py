import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, VIDEO_CARD, \
    SOLID_STATE_DRIVE, STORAGE_DRIVE, COMPUTER_CASE, PROCESSOR, RAM, MONITOR, \
    HEADPHONES, PRINTER, NOTEBOOK, USB_FLASH_DRIVE, STEREO_SYSTEM, \
    GAMING_DESK, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Tecnocam(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            COMPUTER_CASE,
            PROCESSOR,
            RAM,
            MONITOR,
            HEADPHONES,
            PRINTER,
            NOTEBOOK,
            USB_FLASH_DRIVE,
            STEREO_SYSTEM,
            GAMING_DESK,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['placas-madre', MOTHERBOARD],
            ['tarjetas-de-video', VIDEO_CARD],
            ['discos-ssd', SOLID_STATE_DRIVE],
            ['disco-duros', STORAGE_DRIVE],
            ['gabinetes', COMPUTER_CASE],
            ['procesadores', PROCESSOR],
            ['memorias-ram', RAM],
            ['monitores', MONITOR],
            ['audifonos', HEADPHONES],
            ['impresoras-ecotank', PRINTER],
            ['notebook', NOTEBOOK],
            ['pendrive', USB_FLASH_DRIVE],
            ['audio-y-video/parlante-audio-y-video', STEREO_SYSTEM],
            ['accesorios-pc', GAMING_DESK],
            ['microfonos', MICROPHONE]
        ]
        session = session_with_proxy(extra_args)
        products_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://tecnocam.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'content-area').findAll(
                    'div', 'product-loop-wrapper')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    products_url = \
                        container.find('h4', 'product-title').find('a')['href']
                    products_urls.append(products_url)
                page += 1
        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        price_container = soup.find('p', 'price')
        if price_container.find('ins'):
            price = Decimal(remove_words(price_container.find('ins').text))
        else:
            price = Decimal(remove_words(price_container.text))
        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]
        if soup.find('span', 'sku'):
            part_number = soup.find('span', 'sku').text.strip()[:45]

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
                picture_urls=picture_urls
            )
            return [p]
        else:
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
                picture_urls=picture_urls
            )
            return [p]
