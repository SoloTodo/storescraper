import html
import json
import logging
import re
from collections import defaultdict
from decimal import Decimal

import requests.utils
from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, VIDEO_CARD, PROCESSOR, MONITOR, \
    TELEVISION, MOTHERBOARD, RAM, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    POWER_SUPPLY, COMPUTER_CASE, CPU_COOLER, TABLET, PRINTER, CELL, \
    EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, MEMORY_CARD, PROJECTOR, \
    VIDEO_GAME_CONSOLE, STEREO_SYSTEM, ALL_IN_ONE, MOUSE, OPTICAL_DRIVE, \
    KEYBOARD, KEYBOARD_MOUSE_COMBO, WEARABLE, UPS, AIR_CONDITIONER, \
    GAMING_CHAIR, MICROPHONE, CASE_FAN, \
    HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class PcFactory(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            VIDEO_CARD,
            PROCESSOR,
            MONITOR,
            TELEVISION,
            MOTHERBOARD,
            RAM,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            CPU_COOLER,
            TABLET,
            PRINTER,
            CELL,
            EXTERNAL_STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            PROJECTOR,
            VIDEO_GAME_CONSOLE,
            STEREO_SYSTEM,
            ALL_IN_ONE,
            MOUSE,
            OPTICAL_DRIVE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            WEARABLE,
            UPS,
            AIR_CONDITIONER,
            GAMING_CHAIR,
            MICROPHONE,
            CASE_FAN,
            HEADPHONES
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)

        if extra_args and 'cookies' in extra_args:
            session.cookies = requests.utils.cookiejar_from_dict(
                extra_args['cookies'])

        product_entries = defaultdict(lambda: [])

        # Productos normales
        url_extensions = [
            ['735', NOTEBOOK],
            ['334', VIDEO_CARD],
            ['272', PROCESSOR],
            ['995', MONITOR],
            ['789', TELEVISION],
            ['292', MOTHERBOARD],
            ['112', RAM],
            ['100', RAM],
            ['266', RAM],
            ['340', STORAGE_DRIVE],
            ['421', STORAGE_DRIVE],
            ['932', STORAGE_DRIVE],
            ['411', STORAGE_DRIVE],
            ['585', SOLID_STATE_DRIVE],
            ['54', POWER_SUPPLY],
            ['16', COMPUTER_CASE],
            ['328', COMPUTER_CASE],
            ['648', CPU_COOLER],
            ['994', TABLET],
            ['262', PRINTER],
            ['5', CELL],
            ['655', CELL],
            ['422', EXTERNAL_STORAGE_DRIVE],
            ['904', EXTERNAL_STORAGE_DRIVE],
            ['218', USB_FLASH_DRIVE],
            ['48', MEMORY_CARD],
            ['46', PROJECTOR],
            ['438', VIDEO_GAME_CONSOLE],
            ['889', STEREO_SYSTEM],
            ['890', STEREO_SYSTEM],
            ['798', STEREO_SYSTEM],
            # ['700', STEREO_SYSTEM],
            ['831', STEREO_SYSTEM],
            ['34', STEREO_SYSTEM],
            ['797', STEREO_SYSTEM],
            ['748', STEREO_SYSTEM],
            ['999', ALL_IN_ONE],
            ['1302', MOUSE],
            ['286', OPTICAL_DRIVE],
            ['1301', KEYBOARD],
            ['418', KEYBOARD_MOUSE_COMBO],
            ['685', WEARABLE],
            ['38', UPS],
            ['1026', AIR_CONDITIONER],
            ['1007', GAMING_CHAIR],
            ['528', MICROPHONE],
            ['647', CASE_FAN],
            ['850', HEADPHONES],
        ]

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            idx = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.pcfactory.cl/a?categoria={}&' \
                              'pagina={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product')

                if not product_containers:
                    if page == 1:
                        raise Exception('Empty category: ' + url_extension)
                    break

                section_tag = soup.find(
                    'div', {'data-menu-categoria': url_extension})
                section = '{} > {}'.format(html.unescape(
                    section_tag['data-menu-path']),
                    section_tag['data-menu']
                )

                for container in product_containers:
                    product_url = 'https://www.pcfactory.cl' + \
                        container.find('a')['href']
                    product_entries[product_url].append(
                        {
                            'category_weight': 1,
                            'section_name': section,
                            'value': idx
                        }
                    )
                    idx += 1
                page += 1

        # Segunda seleccción
        url_extensions = [
            ['liq-celulares', CELL],
            ['liq-tablets', TABLET],
            ['liq-notebook', NOTEBOOK],
            ['liq-aio', ALL_IN_ONE],
            ['liq-tv', TELEVISION],
            ['liq-smart', WEARABLE],
            ['liq-impresoras', PRINTER],
        ]

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://www.pcfactory.cl/{}'.format(url_extension)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('div', 'product')

            if not product_containers:
                continue

            section_tag = soup.find(
                'div', {'data-menu-categoria': url_extension})
            section = '{} > {}'.format(html.unescape(
                section_tag['data-menu-path']),
                section_tag['data-menu']
            )

            for idx, container in enumerate(product_containers):
                product_url = container.find('a')['href']
                product_entries[
                    'https://www.pcfactory.cl' + product_url].append(
                    {
                        'category_weight': 1,
                        'section_name': section,
                        'value': idx + 1
                    }
                )

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        if extra_args and 'cookies' in extra_args:
            session.cookies = requests.utils.cookiejar_from_dict(
                extra_args['cookies'])

        session.get(url)
        res = session.get(
            'https://www.pcfactory.cl/public/scripts/dynamic/initData.js')
        match = re.search(
            r'window.pcFactory.dataGlobal.serverData\s+= (.+);', res.text)
        product_data = json.loads(match.groups()[0])['producto']

        sku = product_data['id_producto']
        part_number = product_data['partno']
        name = product_data['nombre']
        stock = int(product_data['stock_web']) + \
            int(product_data['stock_tienda'])

        # precio_cash for efectivo
        # precio_fpago for tarjeta bancoestado
        offer_price = Decimal(remove_words(product_data['precio_fpago']))
        normal_price = Decimal(remove_words(product_data['precio_normal']))

        picture_urls = [x.split('?')[0] for x in product_data['imagen_1000']]

        if 'LIQ' in name:
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

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
            picture_urls=picture_urls,
            condition=condition
        )
        return [p]

    @classmethod
    def preflight(cls, extra_args=None):
        if extra_args and extra_args.get('queueit'):
            session = session_with_proxy(extra_args)
            res = session.get('https://www.pcfactory.cl/',
                              allow_redirects=False)
            assert res.status_code == 302
            url = res.headers['Location']
            fixed_url = url.replace('http%3A', 'https%3A')
            res = session.get(fixed_url)
            assert res.status_code == 200

            cookies = requests.utils.dict_from_cookiejar(res.cookies)
            return {
                'cookies': cookies
            }
        else:
            return {}
