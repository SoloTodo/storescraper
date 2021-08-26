import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, STORAGE_DRIVE, \
    SOLID_STATE_DRIVE, POWER_SUPPLY, RAM, MOTHERBOARD, PROCESSOR, VIDEO_CARD, \
    CPU_COOLER, KEYBOARD, MOUSE, HEADPHONES, STEREO_SYSTEM, TABLET, \
    VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class TecTec(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            CPU_COOLER,
            KEYBOARD,
            MOUSE,
            HEADPHONES,
            STEREO_SYSTEM,
            TABLET,
            VIDEO_GAME_CONSOLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['laptops-notebooks', NOTEBOOK],
            ['componentes-para-pc/discos-duro', STORAGE_DRIVE],
            ['componentes-para-pc/discos-estado-solido', SOLID_STATE_DRIVE],
            ['componentes-para-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-para-pc/memoria-ram', RAM],
            ['componentes-para-pc/placas-madres', MOTHERBOARD],
            ['componentes-para-pc/procesadores', PROCESSOR],
            ['componentes-para-pc/tarjetas-de-video', VIDEO_CARD],
            ['componentes-para-pc/ventiladores', CPU_COOLER],
            ['perifericos-gamer/teclados', KEYBOARD],
            ['perifericos-gamer/mouse', MOUSE],
            ['perifericos-gamer/headset-audifonos', HEADPHONES],
            ['accesorios-pc/parlantes-barras-de-sonido', STEREO_SYSTEM],
            ['tablets', TABLET],
            ['consolas', VIDEO_GAME_CONSOLE]
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

                url_webpage = 'https://tectec.cl/product-category/{}/page' \
                              '/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

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
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        else:
            stock = int(soup.find('p', 'stock').text.split()[0])
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').find('bdi').
                                         text))
        picture_urls = [tag['src'] for tag in soup.find('div', 'woocommerce'
                                                               '-product'
                                                               '-gallery'
                                                               '').findAll(
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
            picture_urls=picture_urls,
        )
        return [p]
