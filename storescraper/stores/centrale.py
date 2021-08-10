import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, POWER_SUPPLY, RAM, \
    MOTHERBOARD, PROCESSOR, VIDEO_CARD, NOTEBOOK, TABLET, \
    MONITOR, PRINTER, UPS, MOUSE, COMPUTER_CASE, HEADPHONES, STEREO_SYSTEM, \
    ALL_IN_ONE, VIDEO_GAME_CONSOLE, CELL, WEARABLE, TELEVISION, GAMING_CHAIR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Centrale(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            POWER_SUPPLY,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            NOTEBOOK,
            TABLET,
            MONITOR,
            PRINTER,
            UPS,
            MOUSE,
            COMPUTER_CASE,
            HEADPHONES,
            STEREO_SYSTEM,
            ALL_IN_ONE,
            VIDEO_GAME_CONSOLE,
            CELL,
            WEARABLE,
            TELEVISION,
            GAMING_CHAIR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['tecnología/computación/almacenamiento-externo',
             EXTERNAL_STORAGE_DRIVE],
            ['tecnología/partes-y-piezas/almacenamiento',
             SOLID_STATE_DRIVE],
            ['tecnología/partes-y-piezas/fuentes-de-poder', POWER_SUPPLY],
            ['tecnología/partes-y-piezas/memorias-ram', RAM],
            ['tecnología/partes-y-piezas/placas-madres', MOTHERBOARD],
            ['tecnología/partes-y-piezas/procesadores-pc', PROCESSOR],
            ['tecnología/partes-y-piezas/tarjetas-de-video', VIDEO_CARD],
            ['tecnología/computación/notebooks', NOTEBOOK],
            ['tecnología/computación/tablets/', TABLET],
            ['tecnología/computación/all-in-one/', ALL_IN_ONE],
            ['tecnología/entretención/consolas/', VIDEO_GAME_CONSOLE],
            ['tecnologia/monitores-y-proyectores/monitores', MONITOR],
            ['tecnología/impresión-y-oficina/impresoras-laser', PRINTER],
            ['tecnología/impresión-y-oficina/impresoras-tinta', PRINTER],
            ['tecnología/impresión-y-oficina/multifuncionales-laser', PRINTER],
            ['tecnología/impresión-y-oficina/multifuncionales-tinta', PRINTER],
            ['tecnología/impresión-y-oficina/impresoras-fotograficas',
             PRINTER],
            ['tecnología/impresión-y-oficina/plotters', PRINTER],
            ['tecnología/computación/ups-y-reguladores', UPS],
            ['tecnología/computación/kits-teclados-y-mouses', MOUSE],
            ['tecnología/partes-y-piezas/gabinetes-desktop', COMPUTER_CASE],
            ['tecnología/telefonía/smartphones', CELL],
            ['tecnología/electro/smartwatches-electro', WEARABLE],
            ['tecnología/electro/televisores', TELEVISION],
            ['tecnología/audio/sistemas-de-audio', STEREO_SYSTEM],
            ['tecnología/audio/audífonos', HEADPHONES],
            ['tecnologia/muebles-y-sillas/sillas-muebles-y-sillas', GAMING_CHAIR],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://centrale.cl/categoria-producto' \
                              '/{}/page/{}'.format(url_extension,
                                                   page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-small box ')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category; ' + url_extension)
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
        part_number = soup.find('span', {'id': 'solotodo'}).contents[1].strip()

        if not part_number:
            part_number = None

        name = soup.find('h1', 'product-title').text.strip()
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        offer_price = Decimal(remove_words(
            soup.find('div', {'style': 'margin-bottom: -12px;'}).text.split()[
                0]))
        normal_price = Decimal(remove_words(soup.find('div', {
            'style': 'margin-bottom: -10px; margin-top:-20px'}).text.split()[
                                                0]))
        picture_urls = []
        picture_container = soup.find('div', 'product-thumbnails')
        if picture_container:
            for tag in picture_container.findAll('img',
                                                 'attachment'
                                                 '-woocommerce_thumbnail '
                                                 'lazyload'):
                if tag['data-src'].replace('-300x300', '') not in picture_urls:
                    picture_urls.append(
                        tag['data-src'].replace('-300x300', ''))
        elif soup.find('div', 'woocommerce-product-gallery__image'):
            picture_urls.append(
                soup.find('div', 'woocommerce-product-gallery__image').find(
                    'img')['src'])
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
            picture_urls=picture_urls,
            part_number=part_number
        )
        return [p]
