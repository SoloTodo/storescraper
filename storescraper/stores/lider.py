import json
import logging

import time

from collections import defaultdict
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy, \
    check_ean13, HeadlessChrome
from storescraper import banner_sections as bs


class Lider(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'VideoGameConsole',
            'AllInOne',
            'Projector',
            'SpaceHeater',
            'AirConditioner',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'Wearable',
            'Stove',
            'WaterHeater',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['Tecno/TV/Televisores', ['Television'],
             'Tecno > TV > Televisores', 1],
            ['Tecno/TV/Home_Theater', ['StereoSystem'],
             'Tecno > TV > Home Theater', 1],
            ['Tecno/TV/Proyectores', ['Projector'],
             'Tecno > TV > Proyectores', 1],
            ['Tecno/Mundo_Gamer/Computación_Gamer', ['Notebook'],
             'Tecno > Mundo Gamer > Computación Gamer', 1],
            ['Tecno/Mundo_Gamer/Mouse_y_Teclados', ['Mouse'],
             'Tecno > Mundo Gamer > Mouse y Teclados', 1],
            ['Tecno/Mundo_Gamer/Audífonos', ['Headphones'],
             'Tecno > Mundo Gamer > Audífonos', 1],
            ['Tecno/Mundo_Gamer/Consolas', ['VideoGameConsole'],
             'Tecno > Mundo Gamer > Consolas', 1],
            ['Tecno/Mundo_Gamer/MSI', ['Notebook'],
             'Tecno > Mundo Gamer > MSI', 1],
            ['Tecno/Mundo_Gamer/ASUS', ['Notebook'],
             'Tecno > Mundo Gamer > ASUS', 1],
            ['Tecno/Audio', ['StereoSystem'],
             'Tecno > Audio', 1],
            ['Tecno/Audio/Equipos_de_Música_y_Karaoke', ['StereoSystem'],
             'Tecno > Audio > Equipos de Música y Karaoke', 1],
            ['Tecno/Audio/Soundbars_y_Home_Theater', ['StereoSystem'],
             'Tecno > Audio > Equipos de Música y Karaoke', 1],
            ['Tecno/Audio/Audio_Portable', ['StereoSystem'],
             'Tecno > Audio > Audio Portable', 1],
            ['Tecno/Audio/Micro_y_Mini_Componentes', ['StereoSystem'],
             'Tecno > Audio > Micro y Mini Componentes', 1],
            ['Tecno/Audio/Audífonos', ['Headphones'],
             'Tecno > Audio > Audífonos', 1],
            ['Tecno/Audio/Tornamesas_y_Vinilos', ['StereoSystem'],
             'Tecno > Audio > Tornamesas y Vinilos', 1],
            ['Tecno/Audio/Audio_HI-FI', ['StereoSystem'],
             'Tecno > Audio > Audio HI-FI', 1],
            ['Tecno/Smart_Home/Proyectores', ['Projector'],
             'Tecno > Smart Home > Proyectores', 1],
            ['Tecno/Smart_Home/Aspiradoras_Robot', ['VacuumCleaner'],
             'Tecno > Smart Home > Aspiradoras Robot', 1],
            ['Tecno/Videojuegos/Consolas', ['VideoGameConsole'],
             'Tecno > Videojuegos > Consolas', 1],
            ['Tecno/Videojuegos/Nintendo', ['VideoGameConsole'],
             'Tecno > Videojuegos > Nintendo', 1],
            ['Tecno/Videojuegos/PlayStation', ['VideoGameConsole'],
             'Tecno > Videojuegos > PlayStation', 1],
            ['Tecno/Videojuegos/XBOX', ['VideoGameConsole'],
             'Tecno > Videojuegos > XBOX', 1],
            ['Tecno/Computación/Computadores', ['Notebook'],
             'Tecno > Computación > Computadores', 1],
            ['Tecno/Computación/Impresión', ['Printer'],
             'Tecno > Computación > Impresión', 1],
            ['Tecno/Computación/Tablets', ['Tablet'],
             'Tecno > Computación > Tablets', 1],
            ['Tecno/Computación/Almacenamiento', ['ExternalStorageDrive'],
             'Tecno > Computación > Almacenamiento', 1],
            ['Tecno/Computación/Monitores', ['Monitor'],
             'Tecno > Computación > Monitores', 1],
            ['Tecno/Tecnología_Portable/Audífonos', ['Headphones'],
             'Tecno > Tecnología Portable > Audífonos', 1],
            ['Tecno/Tecnología_Portable/Parlantes', ['StereoSystem'],
             'Tecno > Tecnología Portable > Parlantes', 1],
            ['Tecno/Tecnología_Portable/Wearables', ['Wearable'],
             'Tecno > Tecnología Portable > Wearables', 1],
            ['Tecno/Tecnología_Portable/Consolas', ['VideoGameConsole'],
             'Tecno > Tecnología Portable > Consolas', 1],
            ['Tecno/Tecnología_Portable/Consolas', ['VideoGameConsole'],
             'Tecno > Tecnología Portable > Consolas', 1],
            ['Celulares/Celulares_y_Teléfonos', ['Cell'],
             'Celulares > Celulares y Teléfonos', 1],
            ['Celulares/Smartwatches_y_Wearables', ['Wearable'],
             'Celulares > Smartwatches y Wearables', 1],
            ['Computación/Computadores/Notebooks', ['Notebook'],
             'Computación > Computadores > Notebooks', 1],
            ['Computación/Computadores/Tablets', ['Tablet'],
             'Computación > Computadores > Tablets', 1],
            ['Computación/Computadores/Computadores_All_in_One', ['AllInOne'],
             'Computación > Computadores > Computadores All in One', 1],
            ['Computación/Computadores/Monitores_y_Proyectores', ['Monitor'],
             'Computación > Computadores > Monitores y Proyectores', 1.0],
            ['Computación/Computadores/Accesorios_Computación', ['Mouse'],
             'Computación > Computadores > Accesorios Computación', 1.0],
            ['Computación/Mundo_Gamer/Computación_Gamer', ['Notebook'],
             'Computación > Mundo Gamer > Computación Gamer', 1.0],
            ['Computación/Mundo_Gamer/Mouse_y_Teclados', ['Keyboard'],
             'Computación > Mundo Gamer > Mouse y Teclados', 1.0],
            ['Computación/Mundo_Gamer/Audífonos', ['Headphones'],
             'Computación > Mundo Gamer > Audífonos', 1.0],
            ['Computación/Mundo_Gamer/Consolas', ['VideoGameConsole'],
             'Computación > Mundo Gamer > Consolas', 1.0],
            ['Computación/Mundo_Gamer/MSI', ['Notebook'],
             'Computación > Mundo Gamer > MSI', 1.0],
            ['Computación/Mundo_Gamer/ASUS', ['Notebook'],
             'Computación > Mundo Gamer > ASUS', 1.0],
            ['Computación/Impresión/Impresoras_y_Multifuncionales',
             ['Printer'],
             'Computación > Impresión > Impresoras y Multifuncionales', 1.0],
            ['Computación/Impresión/Impresoras_Láser', ['Printer'],
             'Computación > Impresión > Impresoras Láser', 1.0],
            ['Computación/Almacenamiento/Discos_Duros',
             ['ExternalStorageDrive'],
             'Computación > Almacenamiento > Discos Duros', 1.0],
            ['Computación/Almacenamiento/Discos_Duros_SSD',
             ['SolidStateDrive'],
             'Computación > Almacenamiento > Discos Duros SSD', 1.0],
            ['Computación/Almacenamiento/Tarjetas_de_Memoria',
             ['MemoryCard'],
             'Computación > Almacenamiento > Tarjetas de Memoria', 1.0],
            ['Computación/Almacenamiento/Pendrives', ['UsbFlashDrive'],
             'Computación > Almacenamiento > Pendrives', 1.0],
            ['Electrohogar/Lavado y Planchado',
             ['WashingMachine'],
             'Electrohogar > Lavado y secado', 1.0],
            ['Electrohogar/Lavado_y_secado/Lavavajillas', ['DishWasher'],
             'Electrohogar > Lavado y secado > Lavavajillas', 1.0],
            ['Electrohogar/Refrigeración', ['Refrigerator'],
             'Electrohogar > Refrigeración', 1.0],
            ['Electrohogar/Refrigeración/Freezers', ['Refrigerator'],
             'Electrohogar > Refrigeración > Freezers', 1.0],
            ['Electrohogar/Refrigeración/Frigobar', ['Refrigerator'],
             'Electrohogar > Refrigeración > Frigobar', 1.0],
            ['Electrohogar/Refrigeración/Refrigeradores_No_Frost',
             ['Refrigerator'],
             'Electrohogar > Refrigeración > Refrigeradores No Frost', 1.0],
            ['Electrohogar/Refrigeración/Refrigeradores_Side_By_Side',
             ['Refrigerator'],
             'Electrohogar > Refrigeración > Refrigeradores Side By Side',
             1.0],
            ['Electrohogar/Refrigeración/Refrigeradores_Frio_Directo',
             ['Refrigerator'],
             'Electrohogar > Refrigeración > Refrigeradores Frio Directo',
             1.0],
            ['Electrohogar/Climatización/Aire_acondicionado',
             ['AirConditioner'],
             'Electrohogar > Climatización > Aire acondicionado',
             1.0],
            ['Electrohogar/Electrodomésticos/Aspiradoras__y_Limpieza',
             ['VacuumCleaner'],
             'Electrohogar > Electrodomésticos > Aspiradoras y Limpieza',
             1.0],
            ['Electrohogar/Electrodomésticos/Microondas',
             ['Oven'],
             'Electrohogar > Electrodomésticos > Microondas',
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
        query_url = 'https://buysmart-bff-production.lider.cl/' \
                    'buysmart-bff/category'

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

                session.headers['content-type'] = 'application/json'
                response = session.post(query_url, json.dumps(query_params))
                data = json.loads(response.text)

                if not data['products']:
                    logging.warning('Empty category: ' + category_id)

                for idx, entry in enumerate(data['products']):
                    product_url = 'https://www.lider.cl/product/sku/{}'\
                        .format(entry['sku'])
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
            product_url = 'https://www.lider.cl/product/sku/{}' \
                .format(entry['sku'])
            product_urls.append(product_url)

            if len(product_urls) == threshold:
                return product_urls

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        sku_id = url.split('/')[-1]

        query_url = 'https://buysmart-bff-production.lider.cl/buysmart-bff/' \
                    'products/{}?appId=BuySmart'.format(sku_id)

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
            sku_url = 'https://www.lider.cl/catalogo/product/sku/' + \
                      livechat_sku
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
