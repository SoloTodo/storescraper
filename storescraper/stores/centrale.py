import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE,  USB_FLASH_DRIVE, POWER_SUPPLY, RAM, \
    MOTHERBOARD, PROCESSOR, VIDEO_CARD, NOTEBOOK, TABLET, \
    MONITOR, PRINTER, UPS, MOUSE, COMPUTER_CASE, HEADPHONES, STEREO_SYSTEM
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
            STEREO_SYSTEM
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['tecnologia/computación/almacenamiento-externo',
             EXTERNAL_STORAGE_DRIVE],
            ['tecnologia/partes-y-piezas/almacenamiento',
             SOLID_STATE_DRIVE],
            ['tecnologia/partes-y-piezas/fuentes-de-poder', POWER_SUPPLY],
            ['tecnologia/partes-y-piezas/memorias-ram', RAM],
            ['tecnologia/partes-y-piezas/placas-madres', MOTHERBOARD],
            ['tecnologia/partes-y-piezas/procesadores-pc', PROCESSOR],
            ['tecnologia/partes-y-piezas/tarjetas-de-video', VIDEO_CARD],
            ['tecnologia/computación/notebooks', NOTEBOOK],
            ['tecnologia/computación/tablets/', TABLET],
            ['tecnologia/monitores-proyectores-y-audio/monitores', MONITOR],
            ['tecnologia/impresión-y-oficina/impresoras-laser', PRINTER],
            ['tecnologia/impresión-y-oficina/impresoras-tinta', PRINTER],
            ['tecnologia/impresión-y-oficina/multifuncionales-laser', PRINTER],
            ['tecnologia/impresión-y-oficina/multifuncionales-tinta', PRINTER],
            ['tecnologia/impresión-y-oficina/plotters', PRINTER],
            ['tecnologia/computacion/ups-y-reguladores', UPS],
            ['tecnologia/computación/teclados-y-mouses', MOUSE],
            ['tecnologia/partes-y-piezas/gabinetes-desktop', COMPUTER_CASE],
            ['tecnologia/partes-y-piezas/tarjetas-de-video', HEADPHONES],
            ['tecnologia/partes-y-piezas/tarjetas-de-video', STEREO_SYSTEM]
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
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        if len(soup.find('span', {'id': 'solotodo'}).text.split()) == 1:
            name = soup.find('h1', 'product-title').text.strip()
        else:
            name = soup.find('span', {'id': 'solotodo'}).text.split()[
                       1] + ' - ' + soup.find('h1',
                                              'product-title').text.strip()
        sku = soup.find('button', 'single_add_to_cart_button')['value']
        stock = int(
            soup.find('div', 'add-to-cart-container').find('p').text.split()[
                0])
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
            picture_urls=picture_urls
        )
        return [p]
