import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import STORAGE_DRIVE, POWER_SUPPLY, \
    COMPUTER_CASE, RAM, MONITOR, MOUSE, MOTHERBOARD, PROCESSOR, CPU_COOLER, \
    VIDEO_CARD, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Ingtech(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            HEADPHONES,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOUSE,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_CARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento', STORAGE_DRIVE],
            ['audio', HEADPHONES],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['memorias-ram', RAM],
            ['monitores', MONITOR],
            ['mouse-y-teclado', MOUSE],
            ['placas-madres', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['refrigeracion', CPU_COOLER],
            ['tarjetas-graficas', VIDEO_CARD]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overlfow: ' + url_extension)

                url_webpage = 'https://store.ingtech.cl/categoria-producto/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        key = soup.find('input', {'name': 'comment_post_ID'})['value']
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        sku = soup.find('span', 'sku').text
        normal_price = Decimal(
            remove_words(soup.find('p', 'price').find('bdi').text))
        offer_price = (normal_price * Decimal('0.98')).quantize(0)

        picture_urls = []
        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
