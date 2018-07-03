import json
import re

from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Paris(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
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
            'HomeTheater',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Projector',
            'VideoGameConsole',
            'Monitor',
            'AllInOne',
            'AirConditioner',
            'WaterHeater',
            'SolidStateDrive',
            'SpaceHeater',
            'Smartwatch',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            [None, 'Tecno/Computadores/Notebook', 'Notebook'],
            [None, 'Tecno/Computadores/Apple', 'Notebook'],
            [None, 'Tecno/Computadores/Convertibles 2 en 1', 'Notebook'],
            [None, 'Tecno/Computadores/PC Gamers', 'Notebook'],
            [None, 'Tecno/Gamers/Notebooks', 'Notebook'],
            ['Electro/Televisión', None, 'Television'],
            [None, 'Tecno/Computadores/iPad & Tablet', 'Tablet'],
            ['Línea Blanca/Refrigeración', None, 'Refrigerator'],
            [None, 'Tecno/Impresión/Multifuncionales', 'Printer'],
            [None, 'Tecno/Impresión/Láser', 'Printer'],
            [None, 'Línea Blanca/Cocina/Hornos empotrables', 'Oven'],
            [None, 'Línea Blanca/Cocina/Microondas', 'Oven'],
            [None, 'Línea Blanca/Electrodomésticos/Microondas', 'Oven'],
            [None, 'Línea Blanca/Lavado y Secado/Todas las lavadoras',
             'VacuumCleaner'],
            [None, 'Línea Blanca/Lavado y Secado/Lavadora-Secadoras',
             'WashingMachine'],
            [None, 'Línea Blanca/Lavado y Secado/Secadoras y Centrifugas',
             'WashingMachine'],
            [None, 'Tecno/Celulares/Smartphones', 'Cell'],
            [None, '//Nueva Linea J de Samsung', 'Cell'],
            [None, 'Tecno/Celulares/Básicos', 'Cell'],
            [None, 'Tecno/Fotografía/Cámaras Compactas', 'Camera'],
            [None, 'Tecno/Fotografía/Cámaras Semiprofesionales', 'Camera'],
            [None, 'Electro/Audio/Micro y Minicomponentes', 'StereoSystem'],
            [None, 'Electro/Accesorios para TV/Home Theater', 'HomeTheater'],
            [None, 'Electro/HIFI/Home Cinema', 'HomeTheater'],
            [None, 'Tecno/Accesorios Computación/Discos Duros ',
             'ExternalStorageDrive'],
            [None, 'Tecno/Accesorios Computación/Pendrives', 'UsbFlashDrive'],
            [None, 'Tecno/Accesorios Fotografía/Tarjetas de Memoria',
             'MemoryCard'],
            [None, 'Tecno/Accesorios Computación/Proyectores', 'Projector'],
            [None, 'Tecno/Gamers/Consolas', 'VideoGameConsole'],
            ['Tecno/Consolas VideoJuegos', None, 'VideoGameConsole'],
            [None, 'Tecno/Computadores/Desktop & All-In-One', 'AllInOne'],
            [None, 'Línea Blanca/Climatización/Aire Acondicionado',
             'AirConditioner'],
            [None, 'Línea Blanca/Climatización/Calefont', 'WaterHeater'],
            ['Línea Blanca/Estufas ', None, 'SpaceHeater'],
            [None, 'Tecno/Celulares/Wearables', 'Smartwatch'],
            [None, 'Tecno/Gamers/Teclados y Mouse', 'Mouse'],
            [None, 'Tecno/Accesorios Computación/Mouse y Teclados', 'Mouse'],
            [None, 'Electro/Accesorios para TV/Bluray y DVD',
             'OpticalDiskPlayer'],
            [None, 'Tecno/Gamers/Monitores', 'Monitor'],
            [None, 'Tecno/Accesorios Computación/Monitor Gamer', 'Monitor'],
        ]

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/json'
        product_urls = []

        for cat_2, cat_3, local_category in category_paths:
            if category != local_category:
                continue

            terms = {}

            if cat_2:
                terms['cat_2.raw'] = cat_2

            if cat_3:
                terms['cat_3.raw'] = cat_3

            query = {
                "query": {
                    "function_score": {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "term": terms
                                    }
                                ]
                            }
                        }
                    }
                },
                "size": 1000,
                "from": 0
            }

            response = session.post('https://www.paris.cl/store-api/pyload/'
                                    '_search', json.dumps(query))
            products_data = json.loads(response.text)['hits']['hits']

            if not products_data:
                raise Exception('Empty category: {} {} {}'.format(
                    category, cat_2, cat_3))

            for cell in products_data:
                product_url = cell['_source']['product_can']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/json'

        es_id = re.search(r'/producto/(.+)$', url).groups()[0]

        query = {
            "query": {
                "bool": {
                    "minimum_should_match": 1,
                    "should": [
                        {
                            "term": {
                                "url.keyword": es_id
                            }
                        },
                        {
                            "term": {
                                "children.url.keyword": es_id
                            }
                        }
                    ]
                }
            }
        }

        response = session.post(
            'https://www.paris.cl/store-api/pyload/_search',
            json.dumps(query))
        product_data = json.loads(response.text)['hits']['hits'][0]

        sku = product_data['_id']
        name = product_data['_source']['name']
        description = html_to_markdown(product_data['_source']
                                       ['longDescription'])

        normal_price = Decimal(product_data['_source']['price_internet'])

        offer_price = product_data['_source']['price_tc']
        if offer_price:
            offer_price = Decimal(offer_price)
        else:
            offer_price = normal_price

        # Only use the first child, the other are variations of color for
        # products that don't interest us

        child = product_data['_source']['children'][0]

        if sku.startswith('CB'):
            image_id = sku
            stock = -1
        else:
            image_id = child['ESTILOCOLOR']
            stock = child['stocktienda'] + child['stockcd']

        pictures_resource_url = 'https://imagenes.paris.cl/is/image/' \
                                'Cencosud/{}?req=set,json'.format(image_id)

        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      session.get(pictures_resource_url).text).groups()[0])
        picture_urls = []

        picture_entries = pictures_json['set']['item']
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = 'https://imagenes.paris.cl/is/image/{}?scl=1.0' \
                          ''.format(picture_entry['i']['n'])
            picture_urls.append(picture_url)

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
