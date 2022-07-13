import json
import logging

import time

from collections import defaultdict
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal

from storescraper.categories import AIR_CONDITIONER, ALL_IN_ONE, CELL, \
    DISH_WASHER, EXTERNAL_STORAGE_DRIVE, GAMING_CHAIR, KEYBOARD, MEMORY_CARD, \
    MONITOR, NOTEBOOK, MOUSE, HEADPHONES, OVEN, PRINTER, PROJECTOR, \
    REFRIGERATOR, SOLID_STATE_DRIVE, SPACE_HEATER, STEREO_SYSTEM, TABLET, \
    TELEVISION, USB_FLASH_DRIVE, VACUUM_CLEANER, VIDEO_GAME_CONSOLE, \
    WASHING_MACHINE, WATER_HEATER, WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy, \
    check_ean13, HeadlessChrome
from storescraper import banner_sections as bs


class Lider(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            MONITOR,
            TELEVISION,
            TABLET,
            REFRIGERATOR,
            PRINTER,
            OVEN,
            VACUUM_CLEANER,
            WASHING_MACHINE,
            CELL,
            STEREO_SYSTEM,
            EXTERNAL_STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            VIDEO_GAME_CONSOLE,
            ALL_IN_ONE,
            PROJECTOR,
            SPACE_HEATER,
            AIR_CONDITIONER,
            MOUSE,
            KEYBOARD,
            HEADPHONES,
            WEARABLE,
            WATER_HEATER,
            GAMING_CHAIR,
            SOLID_STATE_DRIVE,
            DISH_WASHER,
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            # TECNO
            ['Tecno/TV/Televisores', [TELEVISION],
             'Tecno > TV > Televisores', 1],
            ['Tecno/TV/Home_Theater', [STEREO_SYSTEM],
             'Tecno > TV > Home Theater', 1],
            ['Tecno/TV/Proyectores', [PROJECTOR],
             'Tecno > TV > Proyectores', 1],
            ['Tecno/Audio', [STEREO_SYSTEM],
             'Tecno > Audio', 1],
            ['Tecno/Audio/Equipos_de_Música_y_Karaoke', [STEREO_SYSTEM],
             'Tecno > Audio > Equipos de Música y Karaoke', 1],
            ['Tecno/Audio/Soundbars_y_Home_Theater', [STEREO_SYSTEM],
             'Tecno > Audio > Equipos de Música y Karaoke', 1],
            ['Tecno/Audio/Audio_Portable', [STEREO_SYSTEM],
             'Tecno > Audio > Audio Portable', 1],
            ['Tecno/Audio/Micro_y_Mini_Componentes', [STEREO_SYSTEM],
             'Tecno > Audio > Micro y Mini Componentes', 1],
            ['Tecno/Audio/Audífonos', [HEADPHONES],
             'Tecno > Audio > Audífonos', 1],
            ['Tecno/Audio/Tornamesas_y_Vinilos', [STEREO_SYSTEM],
             'Tecno > Audio > Tornamesas y Vinilos', 1],
            ['Tecno/Audio/Audio_HI-FI', [STEREO_SYSTEM],
             'Tecno > Audio > Audio HI-FI', 1],
            ['Tecno/Smart_Home/Proyectores', [PROJECTOR],
             'Tecno > Smart Home > Proyectores', 1],
            ['Tecno/Videojuegos/Consolas', [VIDEO_GAME_CONSOLE],
             'Tecno > Videojuegos > Consolas', 1],
            ['Tecno/Videojuegos/Nintendo', [VIDEO_GAME_CONSOLE],
             'Tecno > Videojuegos > Nintendo', 1],
            ['Tecno/Videojuegos/PlayStation', [VIDEO_GAME_CONSOLE],
             'Tecno > Videojuegos > PlayStation', 1],
            ['Tecno/Videojuegos/XBOX', [VIDEO_GAME_CONSOLE],
             'Tecno > Videojuegos > XBOX', 1],
            # CELULARES
            ['Celulares/Celulares_y_Teléfonos', [CELL],
             'Celulares > Celulares y Teléfonos', 1],
            ['Celulares/Smartwatches_y_Wearables', [WEARABLE],
             'Celulares > Smartwatches y Wearables', 1],
            # COMPUTACION
            ['Computación/Computadores/Notebooks', [NOTEBOOK],
             'Computación > Computadores > Notebooks', 1],
            ['Computación/Computadores/Tablets', [TABLET],
             'Computación > Computadores > Tablets', 1],
            ['Computación/Computadores/Computadores_All_in_One', [ALL_IN_ONE],
             'Computación > Computadores > Computadores All in One', 1],
            ['Computación/Computadores/Monitores_y_Proyectores', [MONITOR],
             'Computación > Computadores > Monitores y Proyectores', 1.0],
            ['Computación/Computadores/Accesorios_Computación', [MOUSE],
             'Computación > Computadores > Accesorios Computación', 1.0],
            ['Computación/Mundo_Gamer/Computación_Gamer', [NOTEBOOK],
             'Computación > Mundo Gamer > Computación Gamer', 1.0],
            ['Computación/Mundo_Gamer/Mouse_y_Teclados', [KEYBOARD],
             'Computación > Mundo Gamer > Mouse y Teclados', 1.0],
            ['Computación/Mundo_Gamer/Audífonos', [HEADPHONES],
             'Computación > Mundo Gamer > Audífonos', 1.0],
            ['Computación/Mundo_Gamer/Consolas', [VIDEO_GAME_CONSOLE],
             'Computación > Mundo Gamer > Consolas', 1.0],
            ['Computación/Mundo_Gamer/Sillas_Gamer', [GAMING_CHAIR],
             'Computación > Mundo Gamer > Sillas Gamer', 1],
            ['Computación/Impresión/Impresoras_y_Multifuncionales',
             [PRINTER],
             'Computación > Impresión > Impresoras y Multifuncionales', 1.0],
            ['Computación/Impresión/Impresoras_Láser', [PRINTER],
             'Computación > Impresión > Impresoras Láser', 1.0],
            ['Computación/Almacenamiento/Discos_Duros',
             [EXTERNAL_STORAGE_DRIVE],
             'Computación > Almacenamiento > Discos Duros', 1.0],
            ['Computación/Almacenamiento/Discos_Duros_SSD',
             [SOLID_STATE_DRIVE],
             'Computación > Almacenamiento > Discos Duros SSD', 1.0],
            ['Computación/Almacenamiento/Tarjetas_de_Memoria',
             [MEMORY_CARD],
             'Computación > Almacenamiento > Tarjetas de Memoria', 1.0],
            ['Computación/Almacenamiento/Pendrives', [USB_FLASH_DRIVE],
             'Computación > Almacenamiento > Pendrives', 1.0],
            # ELECTROHOGAR
            ['Electrohogar/Refrigeración', [REFRIGERATOR],
             'Electrohogar > Refrigeración', 1.0],
            ['Electrohogar/Refrigeración/No_Frost',
             [REFRIGERATOR],
             'Electrohogar > Refrigeración > No Frost', 1.0],
            ['Electrohogar/Refrigeración/Frío_Directo',
             [REFRIGERATOR],
             'Electrohogar > Refrigeración > Frio Directo',
             1.0],
            ['Electrohogar/Refrigeración/Side_By_Side', [REFRIGERATOR],
             'Electrohogar > Refrigeración > Side By Side',
             1.0],
            ['Electrohogar/Refrigeración/Freezer', [REFRIGERATOR],
             'Electrohogar > Refrigeración > Freezer', 1.0],
            ['Electrohogar/Refrigeración/Frigobar', [REFRIGERATOR],
             'Electrohogar > Refrigeración > Frigobar', 1.0],
            ['Electrohogar/Lavado_y_Planchado', [WASHING_MACHINE],
             'Electrohogar > Lavado y Planchado', 1.0],
            ['Electrohogar/Lavado_y_Planchado/Lavadoras', [WASHING_MACHINE],
             'Electrohogar > Lavado y Planchado > Lavadoras', 1.0],
            ['Electrohogar/Lavado_y_Planchado/Lavadoras_Secadoras',
             [WASHING_MACHINE],
             'Electrohogar > Lavado y Planchado > Lavadoras Secadoras', 1.0],
            ['Electrohogar/Lavado_y_Planchado/Secadoras', [WASHING_MACHINE],
             'Electrohogar > Lavado y Planchado > Secadoras', 1.0],
            ['Electrohogar/Lavado_y_Planchado/Lavavajillas', [DISH_WASHER],
             'Electrohogar > Lavado y Planchado > Lavavajillas', 1.0],
            ['Electrohogar/Aspiradoras_y_Limpieza', [VACUUM_CLEANER],
             'Electrohogar > Aspiradoras y Limpieza', 1.0],
            ['Electrohogar/Electrodomésticos_Cocina/Hornos_Eléctricos', [OVEN],
             'Electrohogar > Electrodomésticos Cocina > Hornos Eléctricos',
             1.0],
            ['Electrohogar/Electrodomésticos_Cocina/Microondas', [OVEN],
             'Electrohogar > Electrodomésticos Cocina > Microondas', 1.0],
            ['Electrohogar/Cocinas/Hornos_Empotrables', [OVEN],
             'Electrohogar > Cocinas > Hornos Empotrables', 1.0],
            ['Electrohogar/Climatización/Calefacción', [SPACE_HEATER],
             'Electrohogar > Climatización > Calefacción', 1.0],
            ['Electrohogar/Climatización/Termos_y_Calefonts', [WATER_HEATER],
             'Electrohogar > Climatización > Termos y Calefonts', 1.0],
            ['Electrohogar/Climatización/Ventilación/Aire_Acondicionado',
             [AIR_CONDITIONER],
             'Electrohogar > Climatización > Ventilación > Aire Acondicionado',
             1.0],
        ]

        session = session_with_proxy(extra_args)
        product_entries = defaultdict(lambda: [])

        # It's important that the empty one goes first to ensure that the
        # positioning information is preferable based on the default ordering
        sorters = [
            '',
            'price_asc',
            'price_desc',
            'discount_asc',
            'discount_desc',
        ]
        query_url = 'https://apps.lider.cl/catalogo/bff/category'

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            print(category_id)

            local_product_entries = {}

            for sorter in sorters:
                print(sorter)
                query_params = {
                    "categories": category_id,
                    "page": 1,
                    "facets": [],
                    "sortBy": sorter,
                    "hitsPerPage": 1000
                }

                session.headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'PostmanRuntime/7.28.4'
                }
                serialized_params = json.dumps(query_params,
                                               ensure_ascii=False)
                response = session.post(query_url,
                                        serialized_params.encode('utf-8'))
                data = json.loads(response.text)

                if not data['products']:
                    logging.warning('Empty category: ' + category_id)

                for idx, entry in enumerate(data['products']):
                    product_url = 'https://www.lider.cl/catalogo/' \
                                  'product/sku/{}/{}'.format(
                                      entry['sku'], entry.get('slug', 'a'))
                    if product_url not in local_product_entries:
                        local_product_entries[product_url] = {
                            'category_weight': category_weight,
                            'section_name': section_name,
                            'value': idx + 1
                        }

            for product_url, product_entry in local_product_entries.items():
                product_entries[product_url].append(product_entry)

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'PostmanRuntime/7.28.4'
        product_urls = []

        query_url = 'https://529cv9h7mw-dsn.algolia.net/1/indexes/*/' \
                    'queries?x-algolia-application-id=529CV9H7MW&x-' \
                    'algolia-api-key=c6ab9bc3e19c260e6bad42abe143d5f4'

        query_params = {
            "requests": [{
                "indexName": "campaigns_production",
                "params": "query={}&hitsPerPage=1000"
                .format(keyword)}]}

        response = session.post(query_url, json.dumps(query_params))
        data = json.loads(response.text)

        if not data['results'][0]['hits']:
            return []

        for entry in data['results'][0]['hits']:
            product_url = 'https://www.lider.cl/catalogo/product/sku/{}/{}'\
                .format(entry['sku'], entry.get('slug', 'a'))
            product_urls.append(product_url)

            if len(product_urls) == threshold:
                return product_urls

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers = {
            'User-Agent': 'PostmanRuntime/7.28.4'
        }
        sku_id = url.split('/')[-2]

        query_url = 'https://apps.lider.cl/catalogo/bff/products/{}' \
                    .format(sku_id)

        response = session.get(query_url)

        if response.status_code in [500]:
            parsed_extra_args = extra_args or {}
            retries = parsed_extra_args.pop('retries', 5)

            if retries:
                time.sleep(5)
                parsed_extra_args['retries'] = retries - 1
                return cls.products_for_url(
                    url, category=category, extra_args=parsed_extra_args)
            else:
                return []

        entry = json.loads(response.text)

        if not entry.get('success', True):
            return []

        name = '{} {}'.format(entry['brand'], entry['displayName'])
        ean = entry['gtin13']

        if not check_ean13(ean):
            ean = None

        sku = str(entry['sku'])
        stock = -1 if entry['available'] else 0
        normal_price = Decimal(entry['price']['BasePriceSales'])
        offer_price_container = entry['price']['BasePriceTLMC']

        if offer_price_container:
            offer_price = Decimal(offer_price_container)
            if not offer_price:
                offer_price = normal_price

            if offer_price > normal_price:
                offer_price = normal_price
        else:
            offer_price = normal_price

        specs = OrderedDict()
        for spec in entry.get('filters', []):
            specs.update(spec)

        part_number = specs.get('Modelo')
        if part_number:
            part_number = part_number[:49]

        description = None
        if 'longDescription' in entry:
            description = entry['longDescription']

        if description:
            description = html_to_markdown(description)

        picture_urls = ['https://images.lider.cl/wmtcl?source=url'
                        '[file:/productos/{}{}]&sink'.format(sku, img)
                        for img in entry['imagesAvailables']]

        # The preflight method verified that the LiveChat widget is being
        # loaded, and the Google Tag Manager logic that Lider uses to trigger
        # the wiodget makes sure that we only need to check for the brand.
        has_virtual_assistant = entry['brand'] == 'LG'

        return [Product(
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
            ean=ean,
            part_number=part_number,
            picture_urls=picture_urls,
            description=description,
            has_virtual_assistant=has_virtual_assistant
        )]

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://buysmartstatic.lider.cl/' \
                   'landing/json/banners.json?ts={}'

        destination_url_base = 'https://www.lider.cl{}'
        image_url_base = 'https://buysmartstatic.lider.cl/' \
                         'landing/banners/{}'

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'solotodobot'
        banners = []

        url = base_url.format(datetime.now().timestamp())
        response = session.get(url)

        banners_json = json.loads(response.text)
        sliders = banners_json['Slider']

        index = 0

        for slider in sliders:
            if not slider['mobile']:
                destination_urls = [destination_url_base.format(slider['url'])]
                picture_url = image_url_base.format(slider['image'])

                banners.append({
                    'url': destination_url_base.format(''),
                    'picture_url': picture_url,
                    'destination_urls': destination_urls,
                    'key': picture_url,
                    'position': index + 1,
                    'section': bs.HOME,
                    'subsection': 'Home',
                    'type': bs.SUBSECTION_TYPE_HOME
                })

                index += 1

        return banners

    @classmethod
    def preflight(cls, extra_args=None):
        # Query a specific LG SKU in Lider to verify that the LiveChat
        # implementation is up, this will break when the SKU goes
        # out of stock and it needs to be replaced with another

        livechat_sku = extra_args and extra_args.get('livechat_sku', None)

        if not livechat_sku:
            # If no SKU is given, skip validation
            return {}

        with HeadlessChrome() as driver:
            sku_url = 'https://www.lider.cl/catalogo/product/sku/{}/a'.format(
                livechat_sku)
            driver.get(sku_url)

            for i in range(10):
                print(i)
                try:
                    # If livechat is not loaded the command raises an exception
                    driver.execute_script('LC_API')
                    break
                except Exception:
                    # Wait a little and try again in the next iteration
                    time.sleep(1)
            else:
                raise Exception('No LiveChat implementaton found: ' + sku_url)

        return {}
