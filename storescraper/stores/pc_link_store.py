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
            ['accesorios-para-computadores/audifonos-y-manos-libres-2',
             HEADPHONES],
            ['accesorios-para-computadores/kit-teclado-y-mouse-2',
             KEYBOARD_MOUSE_COMBO],
            ['accesorios-para-computadores/microfonos-3', MICROPHONE],
            ['accesorios-para-computadores/mouse', MOUSE],
            ['accesorios-para-computadores/teclado', KEYBOARD],
            ['accesorios-para-computadores/teclados-2', KEYBOARD],
            ['almacenamiento/discos-de-estado-solido', SOLID_STATE_DRIVE],
            ['almacenamiento/discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento/discos-duros-internos', STORAGE_DRIVE],
            ['audio-y-video/auriculares', HEADPHONES],
            ['audio-y-video/parlantes-bocinas-cornetas', STEREO_SYSTEM],
            ['celulares-accesorios/smart-band', WEARABLE],
            ['celulares-accesorios/smartphone', CELL],
            ['celulares-accesorios/smartwatch', WEARABLE],
            ['componentes-informaticos/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-informaticos/gabinetes', COMPUTER_CASE],
            ['componentes-informaticos/modulos-ram-propietarios', RAM],
            ['componentes-informaticos/tarjetas-madre-placas-madre',
             MOTHERBOARD],
            ['componentes-informaticos/procesador', PROCESSOR],
            ['componentes-informaticos/tarjetas-de-video', VIDEO_CARD],
            ['componentes-informaticos/ventiladores-y-sistemas-de-'
             'enfriamiento', CPU_COOLER],
            ['computacion/all-in-one', ALL_IN_ONE],
            ['computacion/notebook', NOTEBOOK],
            ['computacion/tableta', TABLET],
            ['consolas-volantes-accesorios/consolas', VIDEO_GAME_CONSOLE],
            ['impresoras-escaner-suministros/escaner', PRINTER],
            ['impresoras-escaner-suministros/impresoras-ink-jet', PRINTER],
            ['impresoras-escaner-suministros/impresoras-laser', PRINTER],
            ['impresoras-escaner-suministros/impresoras-multifuncionales',
             PRINTER],
            ['memorias-flash-pendrive/pendrive-unidades-flash-usb',
             USB_FLASH_DRIVE],
            ['memorias-flash-pendrive/tarjetas-de-memoria-flash',
             MEMORY_CARD],
            ['monitores-televisores/monitores-2', MONITOR],
            ['monitores-televisores/televisores', TELEVISION],
            ['muebles-sillas-escritorios/escritorios', GAMING_DESK],
            ['muebles-sillas-escritorios/sillas', GAMING_CHAIR],
            # ['perifericos/auriculares-y-manos-libres', HEADPHONES],
            ['kit-teclado-y-mouse-2', KEYBOARD_MOUSE_COMBO],
            ['ups-reguladores/ups-respaldo-de-energia', UPS],
        ]

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = \
            'application/x-www-form-urlencoded'
        session.headers['x-requested-with'] = 'XMLHttpRequest'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://www.pclinkstore.cl/categorias/{}' \
                ''.format(url_extension)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html5lib')

            token = soup.find('meta', {'name': 'csrf-token'})['content']
            id_category = re.search('"id_category":(\d+)', data).groups()[0]

            query_url = 'https://www.pclinkstore.cl/productos'

            page = 1
            done = False
            while not done:
                if page > 50:
                    raise Exception('Page overflow')

                query_params = {
                    "_token": token,
                    "id_category": id_category,
                    "register": 48,
                    "page": page
                }

                product_data = session.post(query_url, query_params).text
                product_json = json.loads(product_data)['data']
                product_soup = BeautifulSoup(product_json, 'html5lib')

                product_containers = product_soup.findAll(
                    'div', 'sv-producto-mod')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for container in product_containers:
                    if 'Avisame' in container.text:
                        done = True
                        break
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')

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
