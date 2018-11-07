import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Hites(Store):
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
            'VideoGameConsole',
            'AllInOne',
            'SpaceHeater',
            'CellAccesory',
            'Keyboard',
            'KeyboardMouseCombo',
            'Mouse',
            'Headphones',
            'ExternalStorageDrive',
            'Monitor',
            'Projector',
            'AirConditioner',
            'WaterHeater',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['electro-hogar/refrigeradores', 'Refrigerator'],
            ['electro-hogar/lavado-y-secado/lavadoras', 'WashingMachine'],
            ['electro-hogar/lavado-y-secado/lavadoras-secadoras',
             'WashingMachine'],
            ['electro-hogar/lavado-y-secado/secadoras', 'WashingMachine'],
            ['electro-hogar/lavado-y-secado/centrifugas', 'WashingMachine'],
            ['electro-hogar/cocina/hornos-empotrados', 'Oven'],
            ['electro-hogar/cocina/hornos-electricos', 'Oven'],
            ['electro-hogar/cocina/microondas', 'Oven'],
            ['electro-hogar/electrodomesticos/hornos-electricos', 'Oven'],
            ['electro-hogar/electrodomesticos/microondas', 'Oven'],
            ['electro-hogar/climatizacion/aire-acondicionado',
             'AirConditioner'],
            ['electro-hogar/climatizacion/estufa-a-lena', 'SpaceHeater'],
            ['electro-hogar/climatizacion/calefont-y-termos', 'WaterHeater'],
            ['tecnologia/tv-video/todos-los-led', 'Television'],
            ['tecnologia/tv-video/dvd-y-blu-ray', 'OpticalDiskPlayer'],
            ['tecnologia/computacion/notebook', 'Notebook'],
            ['tecnologia/computacion/tablets', 'Tablet'],
            ['tecnologia/computacion/impresoras-y-multifuncionales',
             'Printer'],
            ['tecnologia/computacion/pendrive', 'UsbFlashDrive'],
            ['tecnologia/computacion/monitores-y-proyectores', 'Monitor'],
            ['tecnologia/computacion/all-in-one', 'AllInOne'],
            ['tecnologia/computacion/disco-duro', 'ExternalStorageDrive'],
            ['tecnologia/video-juego/consolas', 'VideoGameConsole'],
            ['tecnologia/video-juego/consolas', 'VideoGameConsole'],
            ['tecnologia/audio/parlantes-bluetooth-y-karaokes',
             'StereoSystem'],
            ['tecnologia/audio/minicomponentes', 'StereoSystem'],
            ['tecnologia/audio/hi-fi-y-home-theater', 'StereoSystem'],
            ['tecnologia/audio/microcomponentes', 'StereoSystem'],
            ['tecnologia/audio/audifonos', 'Headphones'],
            ['celulares/accesorios/audifonos', 'Headphones'],
            ['tecnologia/accesorios-y-otros/mouse-y-teclados', 'Mouse'],
            ['tecnologia/accesorios-y-otros/tarjetas-de-memoria',
             'MemoryCard'],
            ['celulares/smartphone/smartphone', 'Cell'],
            ['celulares/smartphone/smartphone-liberados', 'Cell'],
            ['celulares/smartphone/celulares-basicos', 'Cell'],
            ['electro-hogar/electrodomesticos/aspiradoras-y-enceradoras',
             'VacuumCleaner'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_id, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.hites.com/{}?pageSize=48&page={}' \
                               ''.format(category_id, page)

                print(category_url)

                response = session.get(category_url, timeout=30)

                if response.status_code == 500:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                json_data = json.loads(soup.find(
                    'script', {'id': 'hy-data'}).text)

                for product_entry in json_data['result']['products']:
                    slug = product_entry['productString']
                    product_url = 'https://www.hites.com/' + slug
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url, timeout=10).text
        soup = BeautifulSoup(page_source, 'html.parser')
        json_data = json.loads(soup.find('script', {'id': 'hy-data'}).text)[
            'product']

        name = json_data['name']
        sku = json_data['partNumber']

        if json_data['isOutOfStock']:
            stock = 0
            picture_urls = [json_data['fullImage']]
        else:
            stock = -1
            picture_urls = json_data['children'][0]['images']

        normal_price = Decimal(json_data['prices']['offerPrice'])
        offer_price = Decimal(json_data['prices']['cardPrice'])

        description = html_to_markdown(json_data['longDescription'])

        for attribute in json_data['attributes']:
            description += '\n{} {}'.format(attribute['name'],
                                            attribute['value'])

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
