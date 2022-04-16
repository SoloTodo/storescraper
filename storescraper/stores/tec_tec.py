import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, STORAGE_DRIVE, \
    SOLID_STATE_DRIVE, POWER_SUPPLY, RAM, MOTHERBOARD, PROCESSOR, VIDEO_CARD, \
    CPU_COOLER, KEYBOARD, MOUSE, HEADPHONES, STEREO_SYSTEM, TABLET, \
    VIDEO_GAME_CONSOLE, MONITOR
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
            VIDEO_GAME_CONSOLE,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebooks', NOTEBOOK],
            ['monitores', MONITOR],
            ['componentes-para-pc/refrigeracion-cpu', CPU_COOLER],
            ['componentes-para-pc/discos-duro', STORAGE_DRIVE],
            ['componentes-para-pc/discos-estado-solido', SOLID_STATE_DRIVE],
            ['componentes-para-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-para-pc/memoria-ram', RAM],
            ['componentes-para-pc/placas-madres', MOTHERBOARD],
            ['componentes-para-pc/procesadores', PROCESSOR],
            ['componentes-para-pc/tarjetas-de-video', VIDEO_CARD],
            ['perifericos/teclados', KEYBOARD],
            ['perifericos/mouse', MOUSE],
            ['perifericos/headset-audifonos', HEADPHONES],
            ['perifericos/parlantes-barras-de-sonido', STEREO_SYSTEM],
            ['tablets', TABLET],
            ['consolas-y-juegos', VIDEO_GAME_CONSOLE]
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

                url_webpage = 'https://tectec.cl/categoria/{}/page' \
                              '/{}/'.format(url_extension, page)
                # print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-wrapper')

                if not product_containers:
                    if page == 1:
                        print(url_webpage)
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
        name = soup.find('h1', 'product_title').text.strip()
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]

        price_tag = soup.find('p', 'price')

        if not price_tag.text.strip():
            return []
        if price_tag.find('ins'):
            price = Decimal(
                remove_words(price_tag.find('ins').text))
        else:
            price = Decimal(remove_words(price_tag.find('bdi').text))

        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        else:
            stock_tag = soup.find('input', {'name': 'quantity'})
            if not stock_tag:
                stock = 0
            elif 'max' in stock_tag:
                stock = int(stock_tag['max'])
            else:
                stock = int(stock_tag['value'])

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
