import logging
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, STORAGE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, SOLID_STATE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, \
    MOTHERBOARD, PROCESSOR, VIDEO_CARD, MOUSE, KEYBOARD, TELEVISION, MONITOR, \
    MEMORY_CARD, RAM, HEADPHONES, CPU_COOLER, UPS, GAMING_CHAIR, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class CCLink(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            MOUSE,
            KEYBOARD,
            TELEVISION,
            MONITOR,
            MEMORY_CARD,
            RAM,
            HEADPHONES,
            CPU_COOLER,
            UPS,
            GAMING_CHAIR,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computadores/notebook', NOTEBOOK],
            ['partes-y-piezas/almacenamiento/discos-opticos-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['partes-y-piezas/almacenamiento/discos-opticos-internos',
             STORAGE_DRIVE],
            ['partes-y-piezas/almacenamiento/discos-duros-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['partes-y-piezas/almacenamiento/discos-duros-internos',
             STORAGE_DRIVE],
            ['partes-y-piezas/almacenamiento/ssd', SOLID_STATE_DRIVE],
            ['partes-y-piezas/componentes/fuente-de-poder', POWER_SUPPLY],
            ['partes-y-piezas/componentes/gabinetes', COMPUTER_CASE],
            ['partes-y-piezas/componentes/placa-madre', MOTHERBOARD],
            ['partes-y-piezas/componentes/procesadores', PROCESSOR],
            ['partes-y-piezas/componentes/tarjetas-de-video', VIDEO_CARD],
            ['partes-y-piezas/componentes/mouse', MOUSE],
            ['partes-y-piezas/componentes/teclado', KEYBOARD],
            ['partes-y-piezas/componentes/ventiladores', CASE_FAN],
            ['partes-y-piezas/componentes/cooler-cpu', CPU_COOLER],
            ['partes-y-piezas/tv-y-proyeccion/televisores', TELEVISION],
            ['partes-y-piezas/tv-y-proyeccion/monitores', MONITOR],
            ['partes-y-piezas/memorias/flash', MEMORY_CARD],
            ['partes-y-piezas/memorias/ram', RAM],
            ['partes-y-piezas/componentes/gabinetes-gamer', COMPUTER_CASE],
            ['partes-y-piezas/componentes/tarjeta-de-video', VIDEO_CARD],
            ['gamer/juegos-y-consolas/audifonos', HEADPHONES],
            ['energia/ups', UPS],
            ['gamer/comodidad-gamer', HEADPHONES],
            ['gamer/juegos-y-consolas/consolas-xbox', EXTERNAL_STORAGE_DRIVE],
            ['gamer/componentes-rgb', MOTHERBOARD],
            ['gamer/comodidad-gamer/sillas-gamer', GAMING_CHAIR],
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
                url_webpage = 'https://www.cclink.cl/productos/{}/page/{}/'. \
                    format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('ul', {
                    'data-toggle': 'shop-products'})
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('li', 'product'):
                    product_url = \
                        container.find('a', 'woocommerce-LoopProduct-link')[
                            'href']
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
        key = soup.find('button', 'single_add_to_cart_button')['value']
        sku = soup.find('span', 'sku').text.strip()
        stock = -1
        price = Decimal(remove_words(
            soup.find('div', 'product-actions-wrapper').findAll('bdi')[
                0].text))
        picture_urls = [urllib.parse.quote(tag['src'], safe='/:') for tag in
                        soup.find('div', 'product-images-wrapper').findAll(
                            'img')]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls

        )
        return [p]
