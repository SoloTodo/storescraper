import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, PROCESSOR, RAM, \
    MOTHERBOARD, VIDEO_CARD, SOLID_STATE_DRIVE, CPU_COOLER, POWER_SUPPLY, \
    KEYBOARD, MOUSE, HEADPHONES, GAMING_CHAIR, NOTEBOOK, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class InvasionGamer(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            PROCESSOR,
            RAM,
            MOTHERBOARD,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            CPU_COOLER,
            POWER_SUPPLY,
            KEYBOARD,
            MOUSE,
            HEADPHONES,
            GAMING_CHAIR,
            NOTEBOOK,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['gabinetes', COMPUTER_CASE],
            ['procesadores', PROCESSOR],
            ['memoria-ram', RAM],
            ['placas-madre', MOTHERBOARD],
            ['tarjetas-de-video', VIDEO_CARD],
            ['almacenamiento', SOLID_STATE_DRIVE],
            ['refrigeracion', CPU_COOLER],
            ['fuente-de-poder', POWER_SUPPLY],
            ['teclados', KEYBOARD],
            ['mouse', MOUSE],
            ['audifonos', HEADPHONES],
            ['sillas', GAMING_CHAIR],
            ['portatiles', NOTEBOOK],
            ['monitor', MONITOR]
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
                url_webpage = 'https://invasiongamer.com/collections/{}?' \
                              'page={}'.format(url_extension, page)
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
                        'https://invasiongamer.com/' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        variants = soup.find('div', 'product-form__variants')
        name = soup.find('h1', 'product-meta__title').text
        if soup.find('button', {'class': 'product-form__add-button'}).text == \
                'Agotado':
            stock = 0
        else:
            stock = -1
        price = Decimal(
            soup.find('span', 'price').text.split('$')[-1].replace('.', ''))
        picture_urls = ['https:' + tag['data-src'].replace('_130x', '').
                        split('?')[0] for tag in soup
                        .find('div', 'product-gallery__thumbnail-list')
                        .findAll('img')]
        if variants:
            products = []
            for variant in variants.find('select').findAll('option'):
                variant_name = name + ' ' + variant.text
                variant_sku = variant['value']
                p = Product(
                    variant_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    variant_sku,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=variant_sku,
                    picture_urls=picture_urls,
                )
                products.append(p)
            return products
        else:
            sku = soup.find('input', {'name': 'id'})['value']

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
            picture_urls=picture_urls,
        )
        return [p]
