import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, NOTEBOOK, TABLET, HEADPHONES, \
    MOTHERBOARD, PROCESSOR, VIDEO_CARD, RAM, POWER_SUPPLY, COMPUTER_CASE, \
    MONITOR, MOUSE, STORAGE_DRIVE, USB_FLASH_DRIVE, PRINTER, STEREO_SYSTEM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Zacto(Store):
    @classmethod
    def categories(cls):
        return [
            ALL_IN_ONE,
            NOTEBOOK,
            TABLET,
            HEADPHONES,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            RAM,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MONITOR,
            MOUSE,
            STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            PRINTER,
            STEREO_SYSTEM,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['pc-y-portatiles/all-in-one', ALL_IN_ONE],
            ['pc-y-portatiles/notebook', NOTEBOOK],
            ['pc-y-portatiles/tablet', TABLET],
            ['audio-video-y-fotrografia/audifonos', HEADPHONES],
            ['audio-video-y-fotrografia/parlantes', STEREO_SYSTEM],
            ['partes-y-piezas/placas-madre', MOTHERBOARD],
            ['partes-y-piezas/procesadores', PROCESSOR],
            ['partes-y-piezas/tarjeta-de-video', VIDEO_CARD],
            ['partes-y-piezas/memorias-ram', RAM],
            ['partes-y-piezas/fuentes-de-poder', POWER_SUPPLY],
            ['partes-y-piezas/gabinetes', COMPUTER_CASE],
            ['partes-y-piezas/monitores', MONITOR],
            ['partes-y-piezas/mouseteclado-y-mousepad', MOUSE],
            ['almacenamiento/discos-duros', STORAGE_DRIVE],
            ['almacenamiento/pendrives-y-memorias-flash', USB_FLASH_DRIVE],
            ['impresion/impresoras-laser-y-tinta', PRINTER],
            ['impresion/multifuncionales-tinta', PRINTER],
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

                url_webpage = 'https://zacto.cl/categoria/{}/page/' \
                              '{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers or soup.find('div', 'info-404'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for container in product_containers:
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
        key = soup.find('button', {'name': 'add-to-cart'})['value']
        sku_tag = soup.find('span', 'sku')

        if sku_tag:
            sku = soup.find('span', 'sku').text.strip()
        else:
            sku = None

        if soup.find('p', 'stock in-stock'):
            stock = -1
        else:
            stock = 0

        price_tags = soup.findAll('span', 'product-view-cash-price-value')

        assert len(price_tags) == 2

        offer_price = Decimal(remove_words(price_tags[0].text))
        normal_price = Decimal(remove_words(price_tags[1].text))

        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'woocommerce-product-gallery').
                        findAll('img')]
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
            picture_urls=picture_urls
        )
        return [p]
