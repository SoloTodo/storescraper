import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, NOTEBOOK, CELL, UPS, \
    WEARABLE, TABLET, MONITOR, COMPUTER_CASE, MOTHERBOARD, PROCESSOR, RAM, \
    STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, SOLID_STATE_DRIVE, VIDEO_CARD, \
    KEYBOARD_MOUSE_COMBO, MOUSE, KEYBOARD, POWER_SUPPLY, HEADPHONES, \
    GAMING_CHAIR, VIDEO_GAME_CONSOLE, PRINTER, MEMORY_CARD, USB_FLASH_DRIVE, \
    STEREO_SYSTEM
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class Infosep(StoreWithUrlExtensions):
    url_extensions = [
        ['todo-en-uno', ALL_IN_ONE],
        ['notebooks', NOTEBOOK],
        ['celulares', CELL],
        ['reloj-inteligente', WEARABLE],
        ['tablet', TABLET],
        ['monitores', MONITOR],
        ['gabinetes', COMPUTER_CASE],
        ['impresoras-laser', PRINTER],
        ['multifuncionales-laser', PRINTER],
        ['impresoras-de-tinta', PRINTER],
        ['multifuncionales', PRINTER],
        ['plotter', PRINTER],
        ['placas-madres', MOTHERBOARD],
        ['procesadores-intel', PROCESSOR],
        ['procesadores-amd', PROCESSOR],
        ['memorias-pc-notebook', RAM],
        ['disco-hdd', STORAGE_DRIVE],
        ['discos-ssd-externos', EXTERNAL_STORAGE_DRIVE],
        ['discos-ssd-internos', SOLID_STATE_DRIVE],
        ['discos-externos-25', EXTERNAL_STORAGE_DRIVE],
        ['tarjetas-de-video', VIDEO_CARD],
        ['kit-teclado-y-mouse', KEYBOARD_MOUSE_COMBO],
        ['mouse', MOUSE],
        ['teclado', KEYBOARD],
        ['fuente-de-poder-pc', POWER_SUPPLY],
        ['audifonos-gamer', HEADPHONES],
        ['audifonos', HEADPHONES],
        ['fuentes-gamer', POWER_SUPPLY],
        ['gabinetes-gamer', COMPUTER_CASE],
        ['memoria-hyperx', RAM],
        ['motherboard', MOTHERBOARD],
        ['monitor-gamer', MONITOR],
        ['notebook-gaming', NOTEBOOK],
        ['mouse-gamer', MOUSE],
        ['sillas-gamer', GAMING_CHAIR],
        ['teclado-y-mouse-gamer', KEYBOARD_MOUSE_COMBO],
        ['teclado-gamer', KEYBOARD],
        ['tarjetas-de-video-gamer', VIDEO_CARD],
        ['consolas-y-video-juegos', VIDEO_GAME_CONSOLE],
        ['memoria-micro-sdhc', MEMORY_CARD],
        ['pendrive', USB_FLASH_DRIVE],
        ['parlantes', STEREO_SYSTEM],
        ['ups-respaldo-de-energia', UPS],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)
            if page == 1:
                url_webpage = 'https://infosep.cl/categoria-producto/{}/' \
                              ''.format(url_extension)
            else:
                url_webpage = 'https://infosep.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.find('ul', 'products')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers.findAll('li'):
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
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        json_data = json.loads(
            soup.findAll('script', {'type': 'application/ld+json'})[-1]
            .text)

        if '@type' not in json_data:
            return []

        name = json_data['name']
        sku = json_data['sku']
        offer_price = Decimal(json_data['offers'][0]['price'])

        if not offer_price:
            return []

        normal_price = (offer_price * Decimal('1.026')).quantize(0)

        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0

        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]

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
