import json
import logging
import re

from collections import defaultdict
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
    PROJECTOR, CELL


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
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)

        category_paths = [
            ['Q2F0ZWdvcnk6MTIxMQ==', [GAMING_CHAIR],
             'Silla Gamer Profesional', 1],
            ['Q2F0ZWdvcnk6MTIxMw==', [GAMING_DESK], 'Escritorio Gamer', 1],
            ['Q2F0ZWdvcnk6MTIxNQ==', [HEADPHONES], 'Audífono Gamer', 1],
            ['Q2F0ZWdvcnk6MTIxNg==', [MOUSE], 'Mouse Gamer', 1],
            ['Q2F0ZWdvcnk6MTIxOA==', [KEYBOARD], 'Teclado Gamer', 1],
            ['Q2F0ZWdvcnk6MTIxOQ==', [MONITOR], 'Monitor Gamer', 1],
            ['Q2F0ZWdvcnk6MTIyMA==', [KEYBOARD_MOUSE_COMBO],
             'Kit Teclado + Mouse Gamer', 1],
            ['Q2F0ZWdvcnk6MTIyNA==', [NOTEBOOK], 'Notebook Gamer', 1],
            ['Q2F0ZWdvcnk6MTIyNw==', [MICROPHONE], 'Micrófono Streaming', 1],
            ['Q2F0ZWdvcnk6MTIzOA==', [NOTEBOOK], 'Notebooks', 1],
            ['Q2F0ZWdvcnk6MTI3MQ==', [UPS], 'UPS y Respaldo Energía', 1],
            ['Q2F0ZWdvcnk6MTI0Mw==', [ALL_IN_ONE], 'PC All in One', 1],
            ['Q2F0ZWdvcnk6MTI0OA==', [TABLET], 'Tablets', 1],
            ['Q2F0ZWdvcnk6MTI1Mg==', [NOTEBOOK], 'Mac', 1],
            ['Q2F0ZWdvcnk6MTI1Mw==', [TABLET], 'iPad', 1],
            ['Q2F0ZWdvcnk6MTI1NA==', [WEARABLE], 'Apple Watch', 1],
            ['Q2F0ZWdvcnk6MTI1Nw==', [MOUSE], 'Mouse', 1],
            ['Q2F0ZWdvcnk6MTI1OQ==', [KEYBOARD], 'Teclados', 1],
            ['Q2F0ZWdvcnk6MTI2MA==', [STEREO_SYSTEM], 'Parlantes para PC', 1],
            ['Q2F0ZWdvcnk6MTI2MQ==', [MONITOR], 'Monitores', 1],
            ['Q2F0ZWdvcnk6MTI2Mg==', [KEYBOARD_MOUSE_COMBO],
             'Kit Teclado + Mouse Gamer', 1],
            ['Q2F0ZWdvcnk6MTI2Ng==', [USB_FLASH_DRIVE], 'Pendrive', 1],
            ['Q2F0ZWdvcnk6MTI2Nw==', [EXTERNAL_STORAGE_DRIVE],
             'Disco Duro Externo', 1],
            ['Q2F0ZWdvcnk6MTI2OA==', [MEMORY_CARD],
             'Tarjeta Flash Micro SD', 1],
            ['Q2F0ZWdvcnk6MTI4Mg==', [PROCESSOR], 'Procesador', 1],
            ['Q2F0ZWdvcnk6MTMwMA==', [CPU_COOLER], 'Refrigeración Líquida', 1],
            ['Q2F0ZWdvcnk6MTMwMQ==', [CPU_COOLER], 'Disipador CPU', 1],
            ['Q2F0ZWdvcnk6MTMwMg==', [CASE_FAN], 'Ventilador Gabinete', 1],
            ['Q2F0ZWdvcnk6MTI4NQ==', [MOTHERBOARD], 'Placa madre', 1],
            ['Q2F0ZWdvcnk6MTI4OQ==', [RAM], 'Memorias RAM', 1],
            ['Q2F0ZWdvcnk6MTMwNg==', [POWER_SUPPLY], 'Fuente de Poder', 1],
            ['Q2F0ZWdvcnk6MTI5Mw==', [STORAGE_DRIVE],
             'HDD Disco Duro Mecánico', 1],
            ['Q2F0ZWdvcnk6MTI5NA==', [SOLID_STATE_DRIVE],
             'SSD Unidad Estado Sólido', 1],
            ['Q2F0ZWdvcnk6MTMwOA==', [COMPUTER_CASE], 'Gabinetes', 1],
            ['Q2F0ZWdvcnk6MTI5NQ==', [VIDEO_CARD], 'Tarjeta de Video', 1],
            ['Q2F0ZWdvcnk6MTM5Nw==', [PRINTER], 'Plotter', 1],
            ['Q2F0ZWdvcnk6MTM2MQ==', [TELEVISION], 'Televisores', 1],
            ['Q2F0ZWdvcnk6MTM2MQ==', [WEARABLE], 'Smartwatch', 1],
            ['Q2F0ZWdvcnk6MTQwMA==', [WEARABLE], 'Smartwatch', 1],
            ['Q2F0ZWdvcnk6MTM4Mw==', [PROJECTOR], 'Proyectores', 1],
            ['Q2F0ZWdvcnk6MTM4Nw==', [PRINTER], 'Impresoras Láser', 1],
            ['Q2F0ZWdvcnk6MTM4OA==', [PRINTER], 'Impresoras Tinta', 1],
            ['Q2F0ZWdvcnk6MTM5Mw==', [PRINTER], 'Multifuncionales', 1],
            ['Q2F0ZWdvcnk6MTQwNA==', [HEADPHONES], 'Audífonos', 1],
            ['Q2F0ZWdvcnk6MTQwNQ==', [HEADPHONES], 'Audífonos Bluetooth', 1],
            ['Q2F0ZWdvcnk6MTQwNg==', [STEREO_SYSTEM], 'Parlante Portátil', 1],
            ['Q2F0ZWdvcnk6MTQwNw==', [MICROPHONE],
             'Micrófonos y Accesorios', 1],
            ['Q2F0ZWdvcnk6MTQzMA==', [CELL], 'Smartphones', 1],
        ]

        endpoint = 'https://bff.spdigital.cl/api/v1/saleor'
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            cursor = ''
            current_position = 1
            local_product_urls = []

            while True:
                payload = {
                    "query": "query( $channel: String $first: Int $after: "
                             "String $before: String $categories: [ID] "
                             "$collections: [ID] $search: String $metadata: "
                             "[MetadataFilter] $priceGte: Float $priceLte: "
                             "Float $attributes: [AttributeInput] $sortBy: "
                             "ProductOrder $stockAvailability: "
                             "StockAvailability $ids: [ID] ) { products"
                             "( first: $first after: $after before: "
                             "$before channel: $channel filter: { "
                             "isPublished: true, categories: "
                             "$categories, collections: $collections "
                             "price: { gte: $priceGte, lte: $priceLte } "
                             "search: $search metadata: $metadata "
                             "attributes: $attributes stockAvailability: "
                             "$stockAvailability ids: $ids } sortBy: $sortBy "
                             ") { totalCount pageInfo { endCursor startCursor "
                             "hasNextPage hasPreviousPage } edges { node { "
                             "category { id name slug parent { id } } id "
                             "metadata { key value } name slug description "
                             "isAvailable attributes { attribute { name } "
                             "values { name slug } } variants { id name sku "
                             "quantityAvailable media { id type url "
                             "thumbnailUrl: url(size: 100) } } "
                             "defaultVariant { id sku name media { id type "
                             "url thumbnailUrl: url(size: 100) } } media { "
                             "type url thumbnailUrl: url(size: 100) alt } "
                             "thumbnail { url alt } pricing { priceRange { "
                             "start { gross { amount currency } } } } } } } "
                             "} ",
                    "variables": {
                        "channel": "sp-digital",
                        "first": 100,
                        "after": cursor,
                        "before": "",
                        "categories": [category_id],
                        "collections": [],
                        "metadata": [{"key": "pricing"}],
                        "sortBy": {"direction": "ASC", "field": "PRICE"},
                        "priceGte": None,
                        "priceLte": 0,
                        "attributes": [],
                        "stockAvailability": "IN_STOCK",
                        "ids": []
                    }
                }

                print(cursor or 'first')
                response = session.post(endpoint, json=payload)
                products_data = response.json()['data']['products']

                for container in products_data['edges']:
                    product_url = 'https://www.spdigital.cl/{}/'.format(
                        container['node']['slug'])

                    product_entries[product_url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': current_position
                    })

                    local_product_urls.append(product_url)
                    current_position += 1

                if not products_data['pageInfo']['hasNextPage']:
                    break

                cursor = products_data['pageInfo']['endCursor']
        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        slug = re.search('https://www.spdigital.cl/(.+)/$', url).groups()[0]
        page_data_url = 'https://www.spdigital.cl/page-data/{}/' \
                        'page-data.json'.format(slug)
        response = session.get(page_data_url)

        if response.status_code == 403:
            return []

        page_data = response.json()['result']['pageContext']

        name = page_data['content']['name']
        normal_price = Decimal(page_data['content']['pricing']['priceRange']
                               ['start']['gross']['amount'])
        part_number = page_data['productId']
        offer_price = normal_price / Decimal('1.035')

        # Catch both "SELECCION" and "SELECCIÓN"
        if 'SEGUNDA SELECCI' in name:
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        description_json = json.loads(page_data['content']['description'])

        if description_json['blocks'][0]['data']['text']:
            description_tag = BeautifulSoup(
                description_json['blocks'][0]['data']['text'], 'html.parser')
            description = html_to_markdown(description_tag.text)
        else:
            description = None

        picture_urls = [x['url'] for x in page_data['content']['media']]

        products = []

        for variant in page_data['content']['variants']:
            key = variant['sku']
            sku = variant['id']
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
