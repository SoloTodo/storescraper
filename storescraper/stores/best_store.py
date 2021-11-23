import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import POWER_SUPPLY, PROCESSOR, MOTHERBOARD, \
    VIDEO_CARD, CPU_COOLER, NOTEBOOK, TABLET, ALL_IN_ONE, RAM, \
    USB_FLASH_DRIVE, MEMORY_CARD, MONITOR, TELEVISION, HEADPHONES, \
    KEYBOARD_MOUSE_COMBO, STEREO_SYSTEM, COMPUTER_CASE, CELL, \
    STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, SOLID_STATE_DRIVE, UPS
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class BestStore(Store):
    @classmethod
    def categories(cls):
        return [
            POWER_SUPPLY,
            PROCESSOR,
            MOTHERBOARD,
            VIDEO_CARD,
            CPU_COOLER,
            NOTEBOOK,
            TABLET,
            ALL_IN_ONE,
            RAM,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            MONITOR,
            TELEVISION,
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
            STEREO_SYSTEM,
            HEADPHONES,
            STEREO_SYSTEM,
            MONITOR,
            NOTEBOOK,
            COMPUTER_CASE,
            HEADPHONES,
            CELL,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            UPS,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['109-componentes-informaticos-fuentes-de-poder', POWER_SUPPLY],
            ['106-componentes-informaticos-cajas-gabinetes', COMPUTER_CASE],
            ['275-componentes-informaticos-procesadores', PROCESSOR],
            ['180-componentes-informaticos-tarjetas-madre-placas-madre',
             MOTHERBOARD],
            ['181-componentes-informaticos-tarjetas-de-video', VIDEO_CARD],
            ['115-componentes-informaticos-ventiladores-y-sistemas'
             '-de-enfriamiento', CPU_COOLER],
            ['231-computadores-notebook', NOTEBOOK],
            ['236-computadores-tableta', TABLET],
            ['284-computadores-todo-en-uno', ALL_IN_ONE],
            ['232-computadores-computadores-de-mesa', ALL_IN_ONE],
            ['173-memorias-modulos-ram-propietarios', RAM],
            ['194-memorias-modulos-ram-genericos', RAM],
            ['207-memorias-tarjetas-de-memoria-flash', MEMORY_CARD],
            ['209-memorias-unidades-flash-usb', USB_FLASH_DRIVE],
            ['152-monitores-monitores', MONITOR],
            ['233-monitores-televisores', TELEVISION],
            ['117-perifericos-auriculares-y-manos-libres', HEADPHONES],
            ['112-perifericos-combos-de-teclado-y-raton',
             KEYBOARD_MOUSE_COMBO],
            ['160-perifericos-parlantes-bocinas-cornetas', STEREO_SYSTEM],
            ['153-audio-y-video-auriculares', HEADPHONES],
            ['162-audio-y-video-parlantes-bocinas-cornetas', STEREO_SYSTEM],
            ['1097-monitores-gamer', MONITOR],
            ['1098-notebook-gamer', NOTEBOOK],
            ['1101-gabinetes-gamer', COMPUTER_CASE],
            ['1102-auriculares-gamer', HEADPHONES],
            ['228-celulares-celulares-desbloqueados', CELL],
            ['123-almacenamiento-discos-duros-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['198-almacenamiento-almacenamiento-de-redes-nas', STORAGE_DRIVE],
            ['285-almacenamiento-area-de-redes-de-almacenamiento-san',
             STORAGE_DRIVE],
            ['72-discos-duros-servidores', STORAGE_DRIVE],
            ['124-almacenamiento-discos-duros-internos', STORAGE_DRIVE],
            ['146-almacenamiento-discos-de-estado-solido', SOLID_STATE_DRIVE],
            ['127-proteccion-de-poder-ups-respaldo-de-energia', UPS],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 15:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.beststore.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html5lib')
                product_containers = soup.find('div',
                                               {'id': 'js-product-list'})
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.find('div',
                                                         'products row') \
                        .findAll('article'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', {'itemprop': 'name'}).text
        part_number = soup.find('span', {'itemprop': 'sku'}).text
        sku = soup.find('input', {'name': 'id_product'})['value']
        stock_container = soup.find('p', 'en-stock-cantidad')
        if soup.find('p', {'id': 'consultar_stock'}):
            stock = 0
        elif not stock_container:
            stock = -1
        elif stock_container.text.split(':')[-1].strip().startswith('Más'):
            stock = int(stock_container.text.split(':')[-1].strip().split()[2])
        else:
            stock = int(soup.find('p', 'en-stock-cantidad').text.split()[1])
        price_container = soup.findAll('div', 'current-price')
        normal_price = Decimal(remove_words(price_container[1].find('span', {
            'itemprop': 'price'}).text.strip()))
        offer_price = Decimal(remove_words(price_container[0].find('span', {
            'itemprop': 'price'}).text.strip()))
        picture_url = [tag['src'] for tag in
                       soup.find('div', 'images-container').findAll('img')
                       if validators.url(tag['src'])
                       ]
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
            part_number=part_number,
            picture_urls=picture_url
        )
        return [p]
