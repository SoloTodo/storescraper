import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, GAMING_DESK, HEADPHONES, \
    MOUSE, KEYBOARD, KEYBOARD_MOUSE_COMBO, CPU_COOLER, PRINTER, \
    STORAGE_DRIVE, SOLID_STATE_DRIVE, EXTERNAL_STORAGE_DRIVE, RAM, \
    MOTHERBOARD, TELEVISION, UPS, VIDEO_CARD, COMPUTER_CASE, \
    NOTEBOOK, MONITOR, STEREO_SYSTEM, GAMING_CHAIR, TABLET, \
    VIDEO_GAME_CONSOLE, PROCESSOR, MEMORY_CARD, USB_FLASH_DRIVE, CELL, \
    POWER_SUPPLY, MICROPHONE, WEARABLE
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
            TABLET,
            PROCESSOR,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            CELL,
            POWER_SUPPLY,
            MICROPHONE,
            ALL_IN_ONE,
            PRINTER,
            TELEVISION,
            GAMING_DESK,
            UPS,
            WEARABLE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento/discos-de-estado-solido', 54, SOLID_STATE_DRIVE],
            ['almacenamiento/discos-duros-externos', 84,
                EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento/discos-duros-internos', 85, STORAGE_DRIVE],
            ['audio-y-video/auriculares', 30, HEADPHONES],
            ['audio-y-video/microfonos', 196, MICROPHONE],
            ['audio-y-video/parlantes-bocinas-cornetas', 66, STEREO_SYSTEM],
            ['audio-y-video/parlantes-bocinas-cornetas-inteligentes', 97,
                STEREO_SYSTEM],
            ['celulares/celulares-con-servicio', 67, CELL],
            ['celulares/celulares-desbloqueados', 37, CELL],
            ['componentes-informaticos/cajas-gabinetes', 69, COMPUTER_CASE],
            ['componentes-informaticos/fuentes-de-poder', 140, POWER_SUPPLY],
            ['componentes-informaticos/procesadores', 80, PROCESSOR],
            ['componentes-informaticos/tarjetas-de-expansion-de-memoria', 206,
                RAM],
            ['componentes-informaticos/tarjetas-de-video', 60, VIDEO_CARD],
            ['componentes-informaticos/tarjetas-madre-placas-madre', 68,
                MOTHERBOARD],
            ['ventiladores-y-sistemas-de-enfriamiento', 136, CPU_COOLER],
            ['computadores/2-en-1', 208, NOTEBOOK],
            ['computadores/portatiles', 48, NOTEBOOK],
            ['computadores/tableta', 91, TABLET],
            ['computadores/todo-en-uno', 70, ALL_IN_ONE],
            ['impresoras-y-escaneres/escaneres', 102, PRINTER],
            ['impresoras-y-escaneres/impresoras-fotograficas', 185, PRINTER],
            ['impresoras-y-escaneres/impresoras-ink-jet', 169, PRINTER],
            ['impresoras-y-escaneres/impresoras-laser', 77, PRINTER],
            ['impresoras-y-escaneres/impresoras-multifuncionales', 28,
                PRINTER],
            ['memorias/modulos-ram-genericos', 119, RAM],
            ['memorias/modulos-ram-propietarios', 171, RAM],
            ['memorias/tarjetas-de-memoria-flash', 96, MEMORY_CARD],
            ['memorias/unidades-flash-usb', 162, USB_FLASH_DRIVE],
            ['monitores/monitores-2', 25, MONITOR],
            ['monitores/televisores', 93, TELEVISION],
            ['muebles/escritorios', 132, GAMING_DESK],
            ['muebles/sillas', 10, GAMING_CHAIR],
            ['perifericos/auriculares-y-manos-libres', 22, HEADPHONES],
            ['perifericos/combos-de-teclado-y-raton', 146,
                KEYBOARD_MOUSE_COMBO],
            ['perifericos/microfonos-2', 209, MICROPHONE],
            ['perifericos/parlantes-bocinas-cornetas-2', 142, STEREO_SYSTEM],
            ['perifericos/ratones', 63, MOUSE],
            ['perifericos/teclados-y-teclados-de-numeros', 53, KEYBOARD],
            ['proteccion-de-poder/ups-respaldo-de-energia', 19, UPS],
            ['tecnologia-portatil/relojes', 62, WEARABLE],
            ['videojuegos/consolas', 109, VIDEO_GAME_CONSOLE],
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'python-requests/2.21.0'
        session.headers['Content-Type'] = \
            'application/x-www-form-urlencoded'
        session.headers['x-requested-with'] = 'XMLHttpRequest'
        product_urls = []
        for url_extension, id_category, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://www.pclinkstore.cl/categorias/{}' \
                ''.format(url_extension)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')

            token = soup.find('meta', {'name': 'csrf-token'})['content']
            query_url = 'https://www.pclinkstore.cl/productos'
            query_params = {
                "_token": token,
                "id_category": id_category,
                "register": 1000,
            }

            product_data = session.post(query_url, query_params).text
            product_json = json.loads(product_data)['data']
            product_soup = BeautifulSoup(product_json, 'html.parser')

            product_containers = product_soup.findAll('div', 'sv-producto-mod')
            if not product_containers:
                logging.warning('Empty category: ' + url_extension)
                continue

            for container in product_containers:
                if 'Avisame' in container.text:
                    break
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        add_button = soup.find('button', 'add-product-cart')

        if not add_button or 'id' not in add_button.attrs:
            return []

        key = add_button['id']
        name = soup.find('div', 'product-name').text.strip()

        product_infos = soup.findAll('div', 'product-info')
        price_infos = product_infos[0].findAll('div', 'product-price-normal')
        if len(price_infos) == 0:
            price_infos = product_infos[0].findAll(
                'div', 'product-price-discount')
        if len(price_infos) == 1:
            normal_price = offer_price = Decimal(
                remove_words(price_infos[0].find('span').text))
        else:
            offer_price = Decimal(remove_words(
                price_infos[0].find('span').text))
            normal_price = Decimal(remove_words(
                price_infos[1].find('span').text))
            if offer_price > normal_price:
                offer_price = normal_price

        detail_infos = product_infos[1].findAll('p')
        sku = detail_infos[0].text.replace('Número de Parte: ', '')
        stock = int(detail_infos[3].text.split(' ')[2].replace('.', ''))
        if 'NUEVO' in detail_infos[4].text:
            condition = 'https://schema.org/NewCondition'
        else:
            condition = 'https://schema.org/RefurbishedCondition'

        picture_urls = []
        picture_container = soup.find('ul', 'slides')
        for a in picture_container.findAll('a'):
            picture_urls.append(a['href'])

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
            condition=condition,
            picture_urls=picture_urls
        )
        return [p]
