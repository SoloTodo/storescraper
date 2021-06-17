import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, PROCESSOR, MOTHERBOARD, RAM, \
    SOLID_STATE_DRIVE, COMPUTER_CASE, POWER_SUPPLY, CPU_COOLER, MOUSE, \
    KEYBOARD, MONITOR, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class HardwareX(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            SOLID_STATE_DRIVE,
            COMPUTER_CASE,
            POWER_SUPPLY,
            CPU_COOLER,
            MOUSE,
            KEYBOARD,
            MONITOR,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebooks', NOTEBOOK],
            ['procesadores', PROCESSOR],
            ['placas-madre', MOTHERBOARD],
            ['memorias-ram', RAM],
            ['ssd-unidades-de-estado-solido', SOLID_STATE_DRIVE],
            ['gabinetes', COMPUTER_CASE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['cooler-cpu', CPU_COOLER],
            ['mouse-gamer', MOUSE],
            ['teclados-mecanicos-gamer', KEYBOARD],
            ['monitores-gamer-profesionales', MONITOR],
            ['audifonos-headsets-gamer', HEADPHONES]
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
                url_webpage = 'https://www.hardwarex.cl/collections/{}' \
                              '?page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-item')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.hardwarex.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-meta__title').text
        sku = soup.find('input', {'name': 'id'})['value']
        if soup.find('span',
                     'product-form__inventory').text == 'En Stock':
            stock = -1
        else:
            stock = 0
        price = Decimal(soup.find('span', 'price').text.split('$')[-1].
                        replace('.', ''))
        picture_urls = ['https:' + tag['data-zoom'].split('?')[0] for tag in
                        soup.find('div', 'product-gallery')
                            .findAll('img', 'product-gallery__image')]
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
