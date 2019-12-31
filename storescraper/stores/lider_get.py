import json
import urllib

from collections import defaultdict
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy, \
    check_ean13
from storescraper import banner_sections as bs


class LiderGet(Store):
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
            ['Televisores', ['Television'],
             'TV y Video > Televisores', 1],
            ['DVDs_y_Blu-Ray', ['OpticalDiskPlayer'],
             'TV y Video > DVDs y Blu-Ray', 1],
            ['Audífonos', ['Headphones'],
             'Equipos de Audio > Audífonos', 1],
            ['Parlantes_portables', ['StereoSystem'],
             'Equipos de Audio > Parlantes portables', 1],
            ['Equipos_de_música_y_karaokes', ['StereoSystem'],
             'Equipos de Audio > Equipos de música', 1],
            ['Consolas', ['VideoGameConsole'],
             'Videojuegos > Consolas', 1],
            ['Smartphones', ['Cell'],
             'Celulares y Teléfonos > Smartphones', 1],
            # ['Celulares_básicos', ['Cell'],
            #  'Celulares y Teléfonos > Celulares básicos', 1],
            ['Smartwatch', ['Wearable'],
             'Celulares y Teléfonos > Smartwatch', 1],
            ['Tarjetas_de_memoria', ['MemoryCard'],
             'Almacenamiento > Tarjetas de memoria', 1],
            ['Notebooks', ['Notebook'],
             'Computación > Notebooks', 1],
            # ['Convertibles', ['Notebook'],
            #  'Computación > Convertibles', 1],
            # ['Gamers', 'Notebook'],
            ['All_in_One', ['AllInOne'],
             'Computación > All in One', 1],
            ['Tablets', ['Tablet'],
             'Computación > Tablets', 1],
            ['Discos_duros', ['ExternalStorageDrive'],
             'Almacenamiento > Discos duros', 1],
            ['Pendrives', ['UsbFlashDrive'],
             'Almacenamiento > Pendrives', 1],
            ['Impresoras_y_Multifuncionales', ['Printer'],
             'Impresión > Impresoras y Multifuncionales', 1],
            ['Teclados_y_Mouse', ['Mouse', 'Keyboard'],
             'Accesorios de Computación > Teclados y Mouse', 0.5],
            ['Accesorios_Gamers', ['Mouse', 'Keyboard'],
             'Accesorios de Computación > Accesorios Gamers', 0.5],
            ['Lavadoras_superiores', ['WashingMachine'],
             'Lavado y Secado > Lavadoras superiores', 1],
            # ['Lavadoras_frontales', ['WashingMachine'],
            #  'Lavado y Secado > Lavadoras frontales', 1],
            ['Lavadoras_-_secadoras', ['WashingMachine'],
             'Lavado y Secado > Lavadoras - secadoras', 1],
            ['Secadoras', ['WashingMachine'],
             'Lavado y Secado > Secadoras', 1],
            ['Refrigeración', ['Refrigerator'],
             'Refrigeración', 1],
            ['Enfriadores', ['AirConditioner'],
             'Ventilación > Enfriadores', 1],
            ['Aire_acondicionado', ['AirConditioner'],
             'Ventilación > Aire acondicionado', 1],
            ['Encimeras', ['Stove'],
             'Cocina > Encimeras', 1],
            ['Cocina', ['Stove'],
             'Cocina > Cocina', 1],
            ['Horno_Empotrable', ['Oven'],
             'Cocina > Horno Empotrable', 1],
            ['Hornos_eléctricos', ['Oven'],
             '-NO-TITLE- > Hornos eléctricos', 1],
            ['Microondas', ['Oven'],
             '-NO-TITLE- > Microondas', 1],
            ['Calefont', ['WaterHeater'],
             'Calefacción > Calefont', 1],
            ['Estufas_eléctricas', ['SpaceHeater'],
             'Calefacción > Estufas Eléctricas', 1],
            ['Aspiradoras__y_Limpieza', ['VacuumCleaner'],
             'Electrodomésticos > Aspiradoras y Limpieza', 1],
        ]

        session = session_with_proxy(extra_args)
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            query_url = 'https://529cv9h7mw-dsn.algolia.net/1/indexes/*/' \
                        'queries?x-algolia-application-id=529CV9H7MW&x-' \
                        'algolia-api-key=c6ab9bc3e19c260e6bad42abe143d5f4'

            query_params = {
                "requests": [
                    {
                        "indexName": "campaigns_production",
                        "params": "hitsPerPage=1000&facetFilters=%5B%22"
                                  "categorias%3A{}%22%5D".format(
                                    urllib.parse.quote(
                                        category_id.replace('_', ' ')))
                    }
                ]
            }

            response = session.post(query_url, json.dumps(query_params))
            data = json.loads(response.text)

            if not data['results'][0]['hits']:
                raise Exception('Empty category: ' + category_id)

            for idx, entry in enumerate(data['results'][0]['hits']):
                product_url = 'https://www.lider.cl/product/sku/{}'\
                    .format(entry['sku'])
                product_entries[product_url].append({
                    'category_weight': category_weight,
                    'section_name': section_name,
                    'value': idx + 1
                })

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
        session = session_with_proxy(extra_args)
        sku_id = url.split('/')[-1]

        query_url = 'https://buysmart-checkout-bff-production.lider.cl/' \
                    'buysmart-checkout-bff/products/?sku={}&appId=BuySmart' \
                    ''.format(sku_id)
        entry = json.loads(session.get(query_url).text)[0]

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
        else:
            offer_price = normal_price

        specs = OrderedDict()
        for spec in entry.get('filters', []):
            specs.update(spec)

        part_number = specs.get('Modelo')
        if part_number:
            part_number = part_number[:49]

        description = html_to_markdown(entry['longDescription'])

        picture_urls = ['https://images.lider.cl/wmtcl?source=url'
                        '[file:/productos/{}{}]&sink'.format(sku, img)
                        for img in entry['imagesAvailables']]

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
            description=description
        )]

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://productionbuysmart.blob.core.windows.net/' \
                   'landing/json/banners.json?ts={}'

        destination_url_base = 'https://www.lider.cl{}'
        image_url_base = 'https://productionbuysmart.blob.core.windows.net/' \
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
