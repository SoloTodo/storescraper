import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, POWER_SUPPLY, COMPUTER_CASE, \
    RAM, PROCESSOR, CPU_COOLER, VIDEO_CARD, KEYBOARD_MOUSE_COMBO, MOUSE, \
    STEREO_SYSTEM, GAMING_CHAIR, KEYBOARD, MONITOR, GAMING_DESK, MICROPHONE, \
    SOLID_STATE_DRIVE, MOTHERBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class TruluStore(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_CARD,
            KEYBOARD_MOUSE_COMBO,
            MOUSE,
            STEREO_SYSTEM,
            GAMING_CHAIR,
            KEYBOARD,
            MONITOR,
            GAMING_DESK,
            MICROPHONE,
            SOLID_STATE_DRIVE,
            MOTHERBOARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes-pc/almacenamiento', SOLID_STATE_DRIVE],
            ['componentes-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-pc/gabinetes', COMPUTER_CASE],
            ['componentes-pc/memoria-ram', RAM],
            ['componentes-pc/placas-madre', MOTHERBOARD],
            ['componentes-pc/procesadores', PROCESSOR],
            ['componentes-pc/refrigeracion', CPU_COOLER],
            ['componentes-pc/tarjetas-de-video', VIDEO_CARD],
            ['escritorios', GAMING_DESK],
            ['monitores-gamer', MONITOR],
            ['perifericos/audifonos-y-accesorios', HEADPHONES],
            ['perifericos/kit-perifericos', KEYBOARD_MOUSE_COMBO],
            ['perifericos/microfonos', MICROPHONE],
            ['perifericos/mouse', MOUSE],
            ['perifericos/parlantes', STEREO_SYSTEM],
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

                url_webpage = 'https://trulustore.cl/categoria-producto/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-small')

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
        name = soup.find('h1', 'product-title').text.strip()
        sku = soup.find('span', 'sku').text
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        if soup.find('p', 'stock out-of-stock') or 'venta' in name.lower():
            stock = 0
        else:
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        price_container = soup.find('p', 'price')
        if price_container.find('ins'):
            offer_price = Decimal(
                remove_words(price_container.find('ins').text))
        else:
            offer_price = Decimal(
                remove_words(price_container.find('bdi').text))
        normal_price_container = soup.find(
            'p', 'price').find('div', 'ww-price')
        if normal_price_container:
            normal_price = Decimal(
                remove_words(normal_price_container.text))
        else:
            normal_price = offer_price

        picture_tags = soup.find('div', 'product-thumbnails')

        if picture_tags:
            picture_urls = [tag.find('img')['src'] for tag in
                            soup.find('div', 'product-thumbnails').findAll(
                                'noscript')]
        else:
            picture_urls = [
                soup.find('meta', {'property': 'og:image'})['content']
            ]

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
            picture_urls=picture_urls
        )
        return [p]
