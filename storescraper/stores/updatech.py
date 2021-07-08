import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TABLET, SOLID_STATE_DRIVE, PROCESSOR, \
    COMPUTER_CASE, VIDEO_CARD, RAM, STORAGE_DRIVE, POWER_SUPPLY, MOTHERBOARD, \
    EXTERNAL_STORAGE_DRIVE, HEADPHONES, KEYBOARD, MOUSE, \
    KEYBOARD_MOUSE_COMBO, NOTEBOOK, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Updatech(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TABLET,
            SOLID_STATE_DRIVE,
            PROCESSOR,
            COMPUTER_CASE,
            VIDEO_CARD,
            RAM,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            MOTHERBOARD,
            EXTERNAL_STORAGE_DRIVE,
            HEADPHONES,
            KEYBOARD,
            MOUSE,
            KEYBOARD_MOUSE_COMBO,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['portatiles', NOTEBOOK],
            ['tableta', TABLET],
            ['perifericos-2/tabletas-digitales', TABLET],
            ['componentes-pc/discos-de-estado-solido-componentes-pc',
             SOLID_STATE_DRIVE],
            ['componentes-portatil/portatil-ram', RAM],
            ['monitores', MONITOR],
            ['componentes-pc/procesadores-componentes-pc', PROCESSOR],
            ['componentes-pc/gabinetes', COMPUTER_CASE],
            ['componentes-pc/tarjetas-de-video', VIDEO_CARD],
            ['componentes-pc/modulos-ram-genericos', RAM],
            ['componentes-pc/discos-duros-internos', STORAGE_DRIVE],
            ['componentes-pc/fuentes-poder', POWER_SUPPLY],
            ['componentes-pc/placas-madre', MOTHERBOARD],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['componentes-pc/perifericos/auriculares', HEADPHONES],
            ['componentes-pc/perifericos/teclados', KEYBOARD],
            ['componentes-pc/perifericos/mouse', MOUSE],
            ['componentes-pc/perifericos/combos-teclado-y-mouse',
             KEYBOARD_MOUSE_COMBO]
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

                url_webpage = 'https://www.updatech.cl/categoria-producto/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')
                if not product_containers or soup.find('div',
                                                       'error-404 not-found'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    if 'categoria' in product_url:
                        continue
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
        if soup.find('p', 'stock in-stock'):
            stock = -1
        else:
            stock = 0
        if soup.find('p', 'price').find('ins'):
            offer_price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            offer_price = Decimal(remove_words(soup.find('p', 'price').text))

        normal_price = (offer_price * Decimal('1.065')).quantize(0)
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
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
