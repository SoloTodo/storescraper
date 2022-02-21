import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MONITOR, MOUSE, KEYBOARD, GAMING_CHAIR, \
    POWER_SUPPLY, COMPUTER_CASE, PROCESSOR, VIDEO_CARD, MOTHERBOARD, RAM, \
    HEADPHONES, NOTEBOOK, SOLID_STATE_DRIVE, MICROPHONE, CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class GamingHouse(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            MONITOR,
            MOUSE,
            KEYBOARD,
            GAMING_CHAIR,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            RAM,
            HEADPHONES,
            NOTEBOOK,
            SOLID_STATE_DRIVE,
            MICROPHONE,
            CPU_COOLER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['hardware/almacenamiento', SOLID_STATE_DRIVE],
            ['hardware/fuentes-de-poder', POWER_SUPPLY],
            ['hardware/gabinetes', COMPUTER_CASE],
            ['hardware/memorias-ram', RAM],
            ['hardware/placas-madre', MOTHERBOARD],
            ['hardware/procesadores/amd-procesadores/', PROCESSOR],
            ['hardware/procesadores/intel-procesadores/', PROCESSOR],
            ['hardware/refrigeracion-cpu', CPU_COOLER],
            ['hardware/tarjetas-graficas', VIDEO_CARD],
            ['notebooks', NOTEBOOK],
            ['perifericos/audifonos', HEADPHONES],
            ['perifericos/microfonos', MICROPHONE],
            ['perifericos/monitores', MONITOR],
            ['perifericos/mouse', MOUSE],
            ['perifericos/teclados', KEYBOARD],
            ['sillas', GAMING_CHAIR],
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
                url_webpage = 'https://gaming-house.cl/categoria-producto/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-grid-item')

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
        response = session.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        elif soup.find('button', {'name': 'add-to-cart'}):
            stock = -1
        else:
            stock = 0
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))
        picture_urls = [tag['src'] for tag in soup.find('div',
                                                        'woocommerce-product'
                                                        '-gallery').findAll(
            'img')]
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
