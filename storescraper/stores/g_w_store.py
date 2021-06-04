import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, HEADPHONES, \
    COMPUTER_CASE, RAM, PROCESSOR, VIDEO_CARD, MOTHERBOARD, GAMING_CHAIR, \
    KEYBOARD, POWER_SUPPLY, CPU_COOLER, MONITOR, MOUSE, USB_FLASH_DRIVE, \
    STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class GWStore(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            MOTHERBOARD,
            COMPUTER_CASE,
            POWER_SUPPLY,
            RAM,
            USB_FLASH_DRIVE,
            MOUSE,
            KEYBOARD,
            HEADPHONES,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MONITOR,
            CPU_COOLER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['3-procesadores', PROCESSOR],
            ['8-placas-madre', MOTHERBOARD],
            ['12-gabinetes', COMPUTER_CASE],
            ['13-fuentes-de-poder', POWER_SUPPLY],
            ['32-memorias-ram-pc', RAM],
            ['33-memorias-ram-notebook', RAM],
            ['38-memorias-flash', USB_FLASH_DRIVE],
            ['39-pendrives', USB_FLASH_DRIVE],
            ['17-mouse-', MOUSE],
            ['18-teclados', KEYBOARD],
            ['35-audifonos', HEADPHONES],
            ['16-tarjetas-de-video', VIDEO_CARD],
            ['21-nvme', SOLID_STATE_DRIVE],
            ['22-ssd', SOLID_STATE_DRIVE],
            ['23-discos-duros-pc', STORAGE_DRIVE],
            ['49-discos-duros-notebook', STORAGE_DRIVE],
            ['34-disco-duro-externo', EXTERNAL_STORAGE_DRIVE],
            ['43-monitores', MONITOR],
            ['47-refrigeración', CPU_COOLER],
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
                url_webpage = 'https://gwstore.cl/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
                    'article', 'product-miniature')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[1]

        stock_container = soup.find('p', 'stock')
        if stock_container and 'Agotado' in stock_container.text:
            stock = 0
        elif stock_container and 'In stock' in stock_container.text:
            stock = -1
        else:
            stock = int(stock_container.contents[1].split()[0])
        price = Decimal(remove_words(soup.find(
            'span', 'woocommerce-Price-amount').find('bdi').contents[1]))
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'woocommerce-tabs').findAll('img')]
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
