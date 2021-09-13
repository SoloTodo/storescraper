import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, STORAGE_DRIVE, \
    MOTHERBOARD, RAM, POWER_SUPPLY, VIDEO_CARD, COMPUTER_CASE, CPU_COOLER, \
    HEADPHONES, KEYBOARD_MOUSE_COMBO, KEYBOARD, MOUSE, MONITOR, GAMING_CHAIR, \
    PROCESSOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class CafeDigital(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            MOTHERBOARD,
            RAM,
            PROCESSOR,
            POWER_SUPPLY,
            VIDEO_CARD,
            COMPUTER_CASE,
            CPU_COOLER,
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
            KEYBOARD,
            MOUSE,
            MONITOR,
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento-pc/discos-ssd', SOLID_STATE_DRIVE],
            ['almacenamiento-pc/disco-duro-pc-hdd', STORAGE_DRIVE],
            ['placas-madre', MOTHERBOARD],
            ['memorias-pc', RAM],
            ['procesadores', PROCESSOR],
            ['fuentes-de-poder-certificadas', POWER_SUPPLY],
            ['tarjetas-de-video', VIDEO_CARD],
            ['gabinetes-pc', COMPUTER_CASE],
            ['refrigeracion-para-pc/cooler-cpu', CPU_COOLER],
            ['perifericos/audifono', HEADPHONES],
            ['perifericos/combo-kit-teclado-mouse', KEYBOARD_MOUSE_COMBO],
            ['perifericos/teclados', KEYBOARD],
            ['perifericos/mouse', MOUSE],
            ['monitores-pc', MONITOR],
            ['sillas-gamer', GAMING_CHAIR]
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

                url_webpage = 'https://cafedigital.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category' + url_extension)
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
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        else:
            stock = -1

        price_container = soup.find('p', 'price')
        if price_container.text == '':
            return []
        if price_container.find('ins'):
            offer_price = Decimal(
                remove_words(price_container.find('ins').text))
            normal_price = Decimal(
                int(remove_words(price_container.find('ins').text)) * 1.045)
        else:
            offer_price = Decimal(
                remove_words(price_container.text))
            normal_price = Decimal(
                int(remove_words(price_container.text)) * 1.045)
        picture_urls = []
        for tag in soup.find('div', 'product-gallery').findAll('img',
                                                               'lazyload'):
            if tag['src'].startswith('https://'):
                picture_urls.append(tag['src'])
            else:
                picture_urls.append(tag['data-src'])
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
            picture_urls=picture_urls
        )
        return [p]
