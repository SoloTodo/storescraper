import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, VIDEO_CARD, MOTHERBOARD, \
    RAM, STORAGE_DRIVE, SOLID_STATE_DRIVE, POWER_SUPPLY, HEADPHONES, \
    PROCESSOR, MOUSE, KEYBOARD, KEYBOARD_MOUSE_COMBO
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class PcNexus(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            VIDEO_CARD,
            MOTHERBOARD,
            RAM,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            HEADPHONES,
            PROCESSOR,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes/tarjetas-de-video', VIDEO_CARD],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/placas-madre', MOTHERBOARD],
            ['componentes/memorias-ram', RAM],
            ['componentes/discos-duros', STORAGE_DRIVE],
            ['componentes/ssd', SOLID_STATE_DRIVE],
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['componentes/gabinetes-gamer', COMPUTER_CASE],
            ['accesorios-y-perifericos/mouse', MOUSE],
            ['accesorios-y-perifericos/teclados', KEYBOARD],
            ['accesorios-y-perifericos/combo-mouse-y-teclado', KEYBOARD],
            ['audio', HEADPHONES],
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

                url_webpage = 'https://pcnexus.cl/product-category/{}/page' \
                              '/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
                    'a', 'woocommerce-LoopProduct-link')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['href']
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
        if soup.find('span', 'stock'):
            stock = int(soup.find('span', 'stock').text.split()[0])
        else:
            stock = 0
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))
        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]
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
