import json
import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import KEYBOARD_MOUSE_COMBO, MOTHERBOARD, RAM, \
    PROCESSOR, VIDEO_CARD, NOTEBOOK, TABLET, HEADPHONES, MOUSE, \
    SOLID_STATE_DRIVE, KEYBOARD, COMPUTER_CASE, MONITOR, STORAGE_DRIVE, \
    POWER_SUPPLY, CPU_COOLER, CELL, WEARABLE, STEREO_SYSTEM, GAMING_CHAIR, \
    USB_FLASH_DRIVE, MEMORY_CARD, MICROPHONE, CASE_FAN, \
    TELEVISION, VIDEO_GAME_CONSOLE, GAMING_DESK


class InfographicsSolutions(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            RAM,
            PROCESSOR,
            VIDEO_CARD,
            NOTEBOOK,
            TABLET,
            HEADPHONES,
            MOUSE,
            SOLID_STATE_DRIVE,
            KEYBOARD,
            COMPUTER_CASE,
            MONITOR,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            CPU_COOLER,
            CELL,
            WEARABLE,
            STEREO_SYSTEM,
            GAMING_CHAIR,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            MICROPHONE,
            CASE_FAN,
            TELEVISION,
            VIDEO_GAME_CONSOLE,
            GAMING_DESK,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['computacion/almacenamiento/discos-duros',
             STORAGE_DRIVE],
            ['computacion/almacenamiento/discos-solidos',
             SOLID_STATE_DRIVE],
            ['computacion/almacenamiento/microsd', MEMORY_CARD],
            ['componentes-de-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-de-pc/tarjetas-de-video', VIDEO_CARD],
            ['componentes-de-pc/memorias-ram', RAM],
            ['componentes-de-pc/procesadores', PROCESSOR],
            ['componentes-de-pc/refrigeracion/ventiladores', CASE_FAN],
            ['componentes-de-pc/refrigeracion/aire', CPU_COOLER],
            ['componentes-de-pc/refrigeracion/liquida', CPU_COOLER],
            ['componentes-de-pc/placas-madres', MOTHERBOARD],
            ['componentes-de-pc/gabinetes', COMPUTER_CASE],
            ['pantallas-monitores', MONITOR],
            ['portatiles-notebook', NOTEBOOK],
            ['tecnologia/television', TELEVISION],
            ['celulares-smarthphones', CELL],
            ['reloj-inteligente-smartwatch', WEARABLE],
            ['tecnologia/fitnesstracker', WEARABLE],
            ['tecnologia/consolas', VIDEO_GAME_CONSOLE],
            ['accesorios/ofimatica-accesorios/audifonos-headset', HEADPHONES],
            ['accesorios/ofimatica-accesorios/kit-teclado-mouse/',
             KEYBOARD_MOUSE_COMBO],
            ['accesorios/ofimatica-accesorios/microfonos/', MICROPHONE],
            ['accesorios/ofimatica-accesorios/mouse', MOUSE],
            ['accesorios/ofimatica-accesorios/parlantes', STEREO_SYSTEM],
            ['accesorios/ofimatica-accesorios/pendrive', USB_FLASH_DRIVE],
            ['accesorios/ofimatica-accesorios/teclados', KEYBOARD],
            ['accesorios/mundo-gamer/audifonos-gamer', HEADPHONES],
            ['accesorios/mundo-gamer/escritorios-gamer', GAMING_DESK],
            ['accesorios/mundo-gamer/microfonos-condensadores/', MICROPHONE],
            ['accesorios/mundo-gamer/mouse-gamer/', MOUSE],
            ['accesorios/mundo-gamer/sillas/', GAMING_CHAIR],
            ['accesorios/mundo-gamer/teclados-gamer/', KEYBOARD],
            ['tecnologia', TABLET],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                url = 'https://infographicssolutions.cl/categoria-producto/' \
                      '{}/page/{}/'.format(category_path, page)

                if page > 10:
                    raise Exception('Page overflow: ' + page)

                res = session.get(url)
                if res.status_code == 404:
                    if page == 1:
                        logging.warning('Invalid category: ' + url)
                    break

                soup = BeautifulSoup(res.text, 'html.parser')
                products = soup.findAll('div', 'product-grid-item')

                for product in products:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')
        key = soup.find('link', {'rel': 'shortlink'})['href'].split(
            '?p=')[1].strip()

        soup_jsons = soup.findAll(
            'script', {'type': 'application/ld+json'})

        if len(soup_jsons) < 2:
            return []

        product_data = json.loads(soup_jsons[1].text)

        if 'name' in product_data:
            name = product_data['name']
            sku = str(product_data['sku'])
            offer_price = Decimal(product_data['offers'][0]['price'])
            normal_price = round(
                (offer_price * Decimal('1.05')).quantize(0), -1)
        else:
            product_data_2 = json.loads(soup.findAll(
                'script', {'type': 'application/ld+json'}
            )[0].text)['@graph']
            name = product_data_2[3]['name']
            wds = soup.find('div', 'wd-single-price')
            if wds.find('div', 'wds-first').find('ins'):
                offer_price = Decimal(
                    wds.find(
                        'div', 'wds-first'
                    ).find('ins').text.split('$')[-1].replace('.', ''))
            else:
                offer_price = Decimal(
                    wds.find(
                        'div', 'wds-first'
                    ).find('bdi').text.split('$')[-1].replace('.', ''))
            normal_price = Decimal(
                wds.find(
                    'div', 'wds-second'
                ).find('span', 'amount').text.split('$')[-1].replace('.', ''))
            sku = key

        stock_container = soup.find('p', 'stock')

        if 'VENTA' in name.upper() and 'PRE' in name.upper():
            # Preventa
            stock = 0
        elif stock_container:
            stock_text = stock_container.text.split(' ')[0]
            if stock_text == 'Agotado':
                stock = 0
            else:
                stock = int(stock_text)
        else:
            stock = -1

        part_number_container = soup.find('span', 'sku')

        if part_number_container:
            part_number = part_number_container.text.strip()
        else:
            part_number = None

        picture_containers = soup.findAll('div', 'product-image-wrap')
        picture_urls = [
            p.find('a')['href'] for p in picture_containers
            if validators.url(p.find('a')['href'])
        ]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))
        if description == 'None\n':
            description = html_to_markdown(
                str(soup.find('div',
                    'woocommerce-product-details__short-description')))

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
            picture_urls=picture_urls,
            description=description,
            part_number=part_number
        )

        return [p]
