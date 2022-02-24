import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import POWER_SUPPLY, KEYBOARD, MOUSE, \
    KEYBOARD_MOUSE_COMBO, STEREO_SYSTEM, CPU_COOLER, HEADPHONES, PROCESSOR, \
    MOTHERBOARD, RAM, SOLID_STATE_DRIVE, VIDEO_CARD, COMPUTER_CASE, MONITOR, \
    CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class GamingStore(Store):
    @classmethod
    def categories(cls):
        return [
            POWER_SUPPLY,
            CPU_COOLER,
            KEYBOARD,
            MOUSE,
            KEYBOARD_MOUSE_COMBO,
            STEREO_SYSTEM,
            HEADPHONES,
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            COMPUTER_CASE,
            SOLID_STATE_DRIVE,
            MONITOR,
            VIDEO_CARD,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes-pc/procesadores', PROCESSOR],
            ['componentes-pc/placa-base', MOTHERBOARD],
            ['componentes-pc/memorias-ram', RAM],
            ['componentes-pc/almacenamiento', SOLID_STATE_DRIVE],
            ['componentes-pc/tarjetas-de-video', VIDEO_CARD],
            ['componentes-pc/gabinetes', COMPUTER_CASE],
            ['componentes-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-pc/refrigeracion/refrigeracion-liquida', CPU_COOLER],
            ['componentes-pc/refrigeracion/ventiladores', CASE_FAN],
            ['accesorios-gaming/teclado-mouse/teclados', KEYBOARD],
            ['accesorios-gaming/teclado-mouse/mouse', MOUSE],
            ['accesorios-gaming/teclado-mouse/kit-teclado-mouse',
             KEYBOARD_MOUSE_COMBO],
            ['accesorios-gaming/parlantes', STEREO_SYSTEM],
            ['accesorios-gaming/audifonos', HEADPHONES],
            ['monitores', MONITOR],
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
                url_webpage = 'https://gamingstore.cl/{}/page/{}/'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'site-content').findAll(
                    'div', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers[-1].findAll(
                        'div', 'product-grid-item'):
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
        if soup.find('button', 'single_add_to_cart_button'):
            sku = soup.find('button', 'single_add_to_cart_button')['value']
        else:
            sku = soup.find('link', {'rel': 'shortlink'})['href'].split('=')[
                -1]

        add_to_cart_button = soup.find('button', {'name': 'add-to-cart'})
        if soup.find('div', 'ddwcpo-preorder-details'):
            stock = 0
        elif not add_to_cart_button or 'pre' in add_to_cart_button.text\
                .lower():
            stock = 0
        else:
            stock = -1
        if not soup.find('div', 'summary-inner').find('bdi'):
            return []
        price = Decimal(
            remove_words(soup.find('div', 'summary-inner').find('bdi').text))
        picture_urls = [tag['data-src'].split('?')[0] for tag in
                        soup.find('div', 'product-images-inner').findAll(
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
