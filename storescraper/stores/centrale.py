import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, MEMORY_CARD, USB_FLASH_DRIVE, POWER_SUPPLY, RAM, \
    MOTHERBOARD, PROCESSOR, VIDEO_CARD, NOTEBOOK, TABLET, TELEVISION, \
    MONITOR, PRINTER, UPS, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Centrale(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            POWER_SUPPLY,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            NOTEBOOK,
            TABLET,
            TELEVISION,
            MONITOR,
            PRINTER,
            UPS,
            MOUSE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computacion/almacenamiento-de-datos/disco-duro-externo',
             EXTERNAL_STORAGE_DRIVE],
            ['computacion/almacenamiento-de-datos/disco-duro-interno',
             SOLID_STATE_DRIVE],
            ['computacion/almacenamiento-de-datos/memoria-flash', MEMORY_CARD],
            ['computacion/almacenamiento-de-datos/pendrive', USB_FLASH_DRIVE],
            ['computacion/componentes-pc/fuentes-de-poder', POWER_SUPPLY],
            ['computacion/componentes-pc/memorias-ram', RAM],
            ['computacion/componentes-pc/placas-madre', MOTHERBOARD],
            ['computacion/componentes-pc/procesadores', PROCESSOR],
            ['computacion/componentes-pc/tarjetas-de-video', VIDEO_CARD],
            ['computacion/computadores/notebook', NOTEBOOK],
            ['computacion/computadores/tablets', TABLET],
            ['computacion/monitor-tv-y-proyectores/televisores', TELEVISION],
            ['computacion/monitor-tv-y-proyectores/tv-monitor', MONITOR],
            ['impresion/impresion-laser', PRINTER],
            ['impresion/impresion-plotter', PRINTER],
            ['impresion/impresion-tinta', PRINTER],
            ['impresion/multifuncional-laser', PRINTER],
            ['impresion/multifuncional-tinta', PRINTER],
            ['impresion/multifuncionales', PRINTER],
            ['computacion/respaldo-de-energia/ups', UPS],
            ['computacion/computadores/accesorios-computacion', MOUSE],
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
