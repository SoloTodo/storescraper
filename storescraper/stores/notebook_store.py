import logging
import re

from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, \
    CPU_COOLER, CELL, TABLET, WEARABLE, NOTEBOOK, ALL_IN_ONE, MEMORY_CARD, \
    RAM, EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    USB_FLASH_DRIVE, UPS, MOUSE, KEYBOARD, KEYBOARD_MOUSE_COMBO, PROCESSOR, \
    VIDEO_CARD, MOTHERBOARD, POWER_SUPPLY, COMPUTER_CASE, MONITOR, \
    TELEVISION, HEADPHONES, STEREO_SYSTEM, PRINTER, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy


class NotebookStore(StoreWithUrlExtensions):
    url_extensions = [
        ['equipos/computadores/portatiles', NOTEBOOK],
        ['equipos/computadores/ultrabooks', NOTEBOOK],
        ['equipos/computadores/todo-en-uno', ALL_IN_ONE],
        ['equipos/computadores/2-en-1', NOTEBOOK],
        ['equipos/computadores/computadores-de-mesa', ALL_IN_ONE],
        ['equipos/almacenamiento/discos-duros-externos',
         EXTERNAL_STORAGE_DRIVE],
        ['equipos/almacenamiento/discos-duros-internos', STORAGE_DRIVE],
        ['equipos/almacenamiento/discos-de-estado-solido', SOLID_STATE_DRIVE],
        ['equipos/almacenamiento/unidades-flash-usb', USB_FLASH_DRIVE],
        ['equipos/perifericos/mouse', MOUSE],
        ['equipos/perifericos/teclados', KEYBOARD],
        ['equipos/perifericos/combos-de-teclado-y-mouse',
         KEYBOARD_MOUSE_COMBO],
        ['equipos/perifericos/teclados-y-teclados-de-numeros', KEYBOARD],
        ['equipos/perifericos/ratones', MOUSE],
        ['equipos/componentes-informaticos/procesadores', PROCESSOR],
        ['equipos/componentes-informaticos/tarjetas-de-video', VIDEO_CARD],
        ['equipos/componentes-informaticos/tarjetas-y-placas-madre',
         MOTHERBOARD],
        ['equipos/componentes-informaticos/fuentes-de-poder', POWER_SUPPLY],
        ['cajas/gabinetes', COMPUTER_CASE],
        ['equipos/componentes-informaticos/ventiladores-y-'
         'sistemas-de-enfriamiento', CPU_COOLER],
        ['equipos/memorias/tarjetas-de-memoria-flash', MEMORY_CARD],
        ['equipos/memorias/ram-para-notebooks', RAM],
        ['equipos/memorias/ram-para-pc-y-servidores', RAM],
        ['ups/respaldo-de-energia', UPS],
        ['equipos/muebles/sillas', UPS],
        ['portabilidad/celulares-y-tablets/celulares-desbloqueados', CELL],
        ['portabilidad/celulares-y-tablets/tablets-ipads', TABLET],
        ['reloj/trackers-de-actividad', WEARABLE],
        ['audio-video-y-foto/monitores-proyectores/monitores', MONITOR],
        ['audio-video-y-foto/monitores-proyectores/televisores', TELEVISION],
        ['audio-video-y-foto/audio-y-video/parlantes', STEREO_SYSTEM],
        ['audio-video-y-foto/audio-y-video/audifonos-y-headset', HEADPHONES],
        ['impresion/impresoras-y-escaneres/impresoras-ink-jet', PRINTER],
        ['impresion/impresoras-y-escaneres/impresoras-laser', PRINTER],
        ['impresion/impresoras-y-escaneres/impresoras-multifuncionales',
         PRINTER],
        ['impresion/impresoras-y-escaneres/impresoras-fotograficas', PRINTER],
        ['impresion/impresoras-y-escaneres/impresoras-plotter', PRINTER],
        ['gaming/equipos/notebooks', NOTEBOOK],
        ['gaming/equipos/monitores', MONITOR],
        ['gaming/componentes/procesadores', MONITOR],
        ['gaming/componentes/placas-madre', MOTHERBOARD],
        ['gaming/componentes/tarjetas-de-video', VIDEO_CARD],
        ['gaming/componentes/memoria-ram', RAM],
        ['gaming/componentes/almacenamiento', SOLID_STATE_DRIVE],
        ['gaming/componentes/enfriamiento', CPU_COOLER],
        ['gaming/componentes/fuentes-de-poder', POWER_SUPPLY],
        ['gaming/componentes/gabinetes', COMPUTER_CASE],
        ['gaming/perifericos/headset', HEADPHONES],
        ['gaming/perifericos/teclados-y-mouse', KEYBOARD_MOUSE_COMBO],
        ['gaming/perifericos/sillas', GAMING_CHAIR],
        ['gaming/videojuegos/consolas', VIDEO_GAME_CONSOLE],
        ['apple/equipos/macbook', NOTEBOOK],
        ['imac-/-mini-/-pro/studio', ALL_IN_ONE],
        ['ipad/ipod', TABLET],
        ['apple/articulos/apple-watch', WEARABLE],
        ['apple-tv/airpods', HEADPHONES],
        ['apple/articulos/perifericos', KEYBOARD],
        ['apple/articulos/monitores-studio', MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []

        page = 1

        while True:
            if page > 15:
                raise Exception('Page overflow')

            url = 'https://notebookstore.cl/{}?page={}'.format(
                url_extension, page)
            print(url)

            soup = BeautifulSoup(session.get(url).text, 'html5lib')
            products = soup.findAll('div', 'product-block')

            if not products:
                if page == 1:
                    logging.warning('Empty category: ' + url)
                break

            for product in products:
                product_url = ('https://notebookstore.cl' +
                               product.find('a')['href'])
                if product_url in product_urls:
                    return product_urls
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url, timeout=60)

        if response.status_code == 404 or response.status_code == 500:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-form_title').text.strip()
        sku = soup.find('span', 'sku_elem').text.strip()

        if not sku:
            sku = re.search(r'"sku":"(.+?)"', response.text).groups()[0]

        key = soup.find('meta', {'property': 'og:id'})['content']

        stock = 0
        stock_container = soup.find('span', 'product-form-stock')

        if stock_container:
            stock = int(stock_container.text.strip())

        normal_price = Decimal(soup.find(
            'meta', {'property':
                     'product:price:amount'})['content']).quantize(0)
        offer_price = (normal_price * Decimal('0.966')).quantize(Decimal(0))

        picture_urls = [x['src'] for x in
                        soup.find('div', 'product-images').findAll('img')
                        if validators.url(x['src'])]

        description = html_to_markdown(
            str(soup.find('div', 'product-description_custom_fields')))

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
            sku=key,
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
