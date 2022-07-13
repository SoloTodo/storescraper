import json
import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, \
    session_with_proxy
from storescraper.categories import GAMING_CHAIR, WEARABLE, \
    EXTERNAL_STORAGE_DRIVE, GAMING_DESK, MICROPHONE, CPU_COOLER, HEADPHONES, \
    MOUSE, KEYBOARD, MONITOR, KEYBOARD_MOUSE_COMBO, NOTEBOOK, UPS, \
    ALL_IN_ONE, TABLET, STEREO_SYSTEM, USB_FLASH_DRIVE, MEMORY_CARD, \
    PROCESSOR, CASE_FAN, MOTHERBOARD, RAM, POWER_SUPPLY, STORAGE_DRIVE, \
    SOLID_STATE_DRIVE, COMPUTER_CASE, VIDEO_CARD, PRINTER, TELEVISION, \
    PROJECTOR, CELL, VIDEO_GAME_CONSOLE


class SpDigital(Store):
    @classmethod
    def categories(cls):
        return [
            GAMING_CHAIR,
            GAMING_DESK,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            MONITOR,
            KEYBOARD_MOUSE_COMBO,
            NOTEBOOK,
            MICROPHONE,
            UPS,
            ALL_IN_ONE,
            TABLET,
            WEARABLE,
            STEREO_SYSTEM,
            USB_FLASH_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MEMORY_CARD,
            PROCESSOR,
            CPU_COOLER,
            CASE_FAN,
            MOTHERBOARD,
            RAM,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            COMPUTER_CASE,
            VIDEO_CARD,
            PRINTER,
            TELEVISION,
            PROJECTOR,
            CELL,
            VIDEO_GAME_CONSOLE,
            POWER_SUPPLY
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        category_paths = [
            ['gaming-y-streaming-sillas-y-escritorios-silla-gamer-profesional',
                GAMING_CHAIR],
            ['gaming-y-streaming-sillas-y-escritorios-escritorio-gamer',
                GAMING_DESK],
            ['monitor-gamer', MONITOR],
            ['gaming-y-streaming-perifericos-gamer-audifonos-gamer',
                HEADPHONES],
            ['gaming-y-streaming-perifericos-gamer-mouse-gamer', MOUSE],
            ['gaming-y-streaming-perifericos-gamer-teclado-gamer', KEYBOARD],
            ['gaming-y-streaming-perifericos-gamer-kit-teclado--mouse-gamer',
                KEYBOARD_MOUSE_COMBO],
            ['gaming-y-streaming-pc-y-notebook-gamer-notebook-gamer',
                NOTEBOOK],
            ['gaming-y-streaming-streaming-microfono-streaming', MICROPHONE],
            ['gaming-y-streaming-consolas-y-controles-controles-y-accesorios',
                VIDEO_GAME_CONSOLE],
            ['computacion-notebook-notebooks', NOTEBOOK],
            ['computacion-pc-pc-all-in-one', ALL_IN_ONE],
            ['computacion-tablet-tablets', TABLET],
            ['computacion-apple-mac', NOTEBOOK],
            ['computacion-apple-ipad', TABLET],
            ['computacion-apple-apple-watch', WEARABLE],
            ['computacion-perifericos-mouse', MOUSE],
            ['computacion-perifericos-teclados', KEYBOARD],
            ['computacion-perifericos-parlantes-para-pc', STEREO_SYSTEM],
            ['computacion-almacenamiento-datos-pendrive', USB_FLASH_DRIVE],
            ['computacion-almacenamiento-datos-disco-duro-externo',
                EXTERNAL_STORAGE_DRIVE],
            ['computacion-almacenamiento-datos-tarjeta-flash-micro-sd',
                MEMORY_CARD],
            ['computacion-ups-y-energia-ups-y-respaldo-energia', UPS],
            ['monitor', MONITOR],
            ['componentes-procesador', PROCESSOR],
            ['componentes-placa-madre', MOTHERBOARD],
            ['componentes-memorias-ram', RAM],
            ['componentes-almacenamiento-hdd-disco-duro-mecanico',
                STORAGE_DRIVE],
            ['componentes-almacenamiento-ssd-unidad-estado-solido',
                SOLID_STATE_DRIVE],
            ['componentes-tarjeta-de-video', VIDEO_CARD],
            ['componentes-refrigeracion-y-ventilacion-refrigeracion-liquida',
                CPU_COOLER],
            ['componentes-refrigeracion-y-ventilacion-disipador-cpu',
                CPU_COOLER],
            ['componentes-refrigeracion-y-ventilacion-ventilador-gabinete',
                CASE_FAN],
            ['componentes-fuente-de-poder', POWER_SUPPLY],
            ['componentes-gabinetes', COMPUTER_CASE],
            ['hogar-y-oficina-television-televisores', TELEVISION],
            ['hogar-y-oficina-equipamiento-oficina-proyectores', PROJECTOR],
            ['hogar-y-oficina-impresoras-impresoras-laser', PRINTER],
            ['hogar-y-oficina-impresoras-impresoras-tinta', PRINTER],
            ['hogar-y-oficina-smartwatches-smartwatch', WEARABLE],
            ['audio-y-musica-audio-audifonos', HEADPHONES],
            ['audio-y-musica-audio-audifonos-bluetooth', HEADPHONES],
            ['audio-y-musica-audio-parlante-portatil', STEREO_SYSTEM],
            ['audio-y-musica-audio-microfonos-y-accesorios', MICROPHONE],
            ['barra-y-sistema-de-sonido', STEREO_SYSTEM],
            ['audio-y-musica-audio-profesional-microfono-profesional',
                MICROPHONE],
            ['otras-categorias-celular-y-accesorios-smartphones', CELL],
        ]

        product_urls = []
        for url_extension, local_category in category_paths:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 100:
                    raise Exception('Page overflow: ' + url_extension)

                if page == 1:
                    url_webpage = 'https://www.spdigital.cl/page-data/' \
                        'categories/{}/page-data.json'.format(url_extension)
                else:
                    url_webpage = 'https://www.spdigital.cl/page-data/' \
                        'categories/{}/{}/page-data.json'.format(
                            url_extension, page)

                response = session.get(url_webpage)

                if response.status_code != 200:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                json_data = json.loads(response.text)[
                    'result']['pageContext']['content']

                for item in json_data['items']:
                    product_urls.append(
                        'https://www.spdigital.cl/' + item['slug'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        slug = url.split('/')[-1]
        page_data_url = 'https://www.spdigital.cl/page-data/{}/' \
                        'page-data.json'.format(slug)
        print(page_data_url)
        response = session.get(page_data_url)

        if response.status_code == 403 or response.status_code == 404:
            return []

        page_data = response.json()['result']['pageContext']

        name = page_data['content']['name']
        part_number = page_data['productId']

        payload = {
            "query": "\n  query($id: ID, $channel: String) {\n      product(id"
            ": $id, channel: $channel) {\n          metadata {\n              "
            "key\n              value\n          }\n          pricing {\n     "
            "         priceRange {\n                  start {\n               "
            "       gross {\n                          amount\n               "
            "           currency\n                      }\n                  }"
            "\n              }\n          }\n          variants {\n           "
            "   id\n              quantityAvailable\n          }\n      }\n  }"
            "\n  ",
            "variables": {
                "channel": "sp-digital",
                "id": page_data['content']['id']
            }
        }
        sale_response = session.post(
            'https://bff.spdigital.cl/api/v1/saleor', json=payload)
        sale_json = json.loads(sale_response.text)

        normal_price = Decimal(sale_json['data']['product']['pricing'][
            'priceRange']['start']['gross']['amount'])

        for metadata_entry in page_data['content']['metadata']:
            if metadata_entry['key'] == 'pricing':
                pricing_json = json.loads(metadata_entry['value'])
                cash_price = Decimal(pricing_json['sp-digital']['cash'])
                other_price = Decimal(pricing_json['sp-digital']['other'])
                break
        else:
            raise Exception('No pricing entry found')

        # I have zero idea why they calculate it like this
        offer_price = (normal_price * cash_price / other_price).quantize(0)

        refurbished_blacklist = [
            'CAJA ABIERTA',
            'SEGUNDA SELECCI',
            'DAÑADA'
        ]

        for keyword in refurbished_blacklist:
            if keyword in name:
                condition = 'https://schema.org/RefurbishedCondition'
                break
        else:
            condition = 'https://schema.org/NewCondition'

        if page_data['content']['description']:
            description_json = json.loads(page_data['content']['description'])

            if description_json['blocks'][0]['data']['text']:
                description_tag = BeautifulSoup(
                    description_json['blocks'][0]['data']['text'],
                    'html.parser')
                description = html_to_markdown(description_tag.text)
            else:
                description = None
        else:
            description = None

        picture_urls = [x['url'] for x in page_data['content']['media']]

        products = []

        for variant in page_data['content']['variants']:
            sku = variant['sku']
            key = variant['id']
            stock = variant['quantityAvailable']

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
                part_number=part_number,
                condition=condition,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products

    @classmethod
    def _retrieve_page(cls, session, url, retries=5):
        print(url)
        try:
            return session.get(url, timeout=90)
        except Exception:
            if retries:
                return cls._retrieve_page(session, url, retries - 1)
            else:
                raise
