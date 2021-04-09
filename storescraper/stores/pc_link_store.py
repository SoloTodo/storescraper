import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MOUSE, KEYBOARD, \
    KEYBOARD_MOUSE_COMBO, CPU_COOLER, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, RAM, MOTHERBOARD, VIDEO_CARD, COMPUTER_CASE, \
    NOTEBOOK, MONITOR, STEREO_SYSTEM, GAMING_CHAIR, TABLET, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class PcLinkStore(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            CPU_COOLER,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            RAM,
            MOTHERBOARD,
            VIDEO_CARD,
            COMPUTER_CASE,
            VIDEO_GAME_CONSOLE,
            NOTEBOOK,
            MONITOR,
            STEREO_SYSTEM,
            GAMING_CHAIR,
            TABLET
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accesorios/audifono-gamers', HEADPHONES],
            ['accesorios/mouse', MOUSE],
            ['accesorios/teclados', KEYBOARD],
            ['accesorios/kit-teclado-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['disipador/water-cooling', CPU_COOLER],
            ['componentes/disco-duro-sata', STORAGE_DRIVE],
            ['componentes/disco-duro-ssd', SOLID_STATE_DRIVE],
            ['componentes/disco-duro-externo', EXTERNAL_STORAGE_DRIVE],
            ['memorias-ram', RAM],
            ['placas-madres', MOTHERBOARD],
            ['tarjetas-de-video', VIDEO_CARD],
            ['componentes/gabinete', COMPUTER_CASE],
            ['consolas', VIDEO_GAME_CONSOLE],
            ['notebook', NOTEBOOK],
            ['monitores', MONITOR],
            ['parlantes', STEREO_SYSTEM],
            ['sillas-gamers', GAMING_CHAIR],
            ['tablet', TABLET]
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
                url_webpage = 'https://www.pclinkstore.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'col-lg-12 col-md-12')
                if not product_containers or not product_containers.findAll(
                        'div', 'col-lg-3'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('div', 'col-lg-3'):
                    product_url = container.find('a')['href']
                    product_urls.append('https://www.pclinkstore.cl' +
                                        product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-form_title').text
        sku = \
            soup.find('form', {'enctype': 'multipart/form-data'})[
                'action'].split('/')[-1]
        if not soup.find('span', 'product-form-stock'):
            stock = 0
        else:
            stock = int(soup.find('span', 'product-form-stock').text)
        price = Decimal(
            remove_words(soup.find('span', 'product-form_price').text))
        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div', 'product-images').findAll('img')]
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
