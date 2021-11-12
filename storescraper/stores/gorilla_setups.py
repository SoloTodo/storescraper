import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, KEYBOARD, MONITOR, HEADPHONES, \
    GAMING_CHAIR, VIDEO_CARD, PROCESSOR, MOTHERBOARD, POWER_SUPPLY, \
    CPU_COOLER, STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, RAM, COMPUTER_CASE, \
    SOLID_STATE_DRIVE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class GorillaSetups(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            KEYBOARD,
            MONITOR,
            HEADPHONES,
            GAMING_CHAIR,
            VIDEO_CARD,
            PROCESSOR,
            MOTHERBOARD,
            POWER_SUPPLY,
            CPU_COOLER,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            RAM,
            COMPUTER_CASE,
            SOLID_STATE_DRIVE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['20-procesadores', PROCESSOR],
            ['13-mouse', MOUSE],
            ['16-teclados', KEYBOARD],
            ['6-monitores', MONITOR],
            ['15-audifonos-', HEADPHONES],
            ['17-sillas-gamer-', GAMING_CHAIR],
            ['19-tarjetas-de-video', VIDEO_CARD],
            ['23-fuente-de-poder', POWER_SUPPLY],
            ['26-refrigeracion-', CPU_COOLER],
            ['28-disco-duro-pcs', STORAGE_DRIVE],
            ['30-disco-externo', EXTERNAL_STORAGE_DRIVE],
            ['21-placas-madres', MOTHERBOARD],
            ['22-memoria-ram', RAM],
            ['24-gabinetes', COMPUTER_CASE],
            ['29-disco-estado-solido-', SOLID_STATE_DRIVE],
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

                url_webpage = 'https://gorillasetups.cl/{}?page={}'.format(
                    url_extension, page)
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', {'itemprop': 'name'}).text
        sku = soup.find('input', {'name': 'id_product'})['value']

        availability_tag = soup.find('link', {'itemprop': 'availability'})

        if availability_tag['href'] == 'https://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        price = Decimal(
            soup.find('div', 'current-price').find('span')['content'])
        picture_urls = [tag['src'] for tag in
                        soup.find('ul', 'product-images').findAll('img')]
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
