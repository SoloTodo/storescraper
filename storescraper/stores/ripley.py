import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Ripley(Store):
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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://simple.ripley.cl/{}?page={}&pageSize=50&orderBy=3'

        category_urls = [
            ['computacion/computadores/notebooks', 'Notebook'],
            ['computacion/computadores/2-en-1-convertibles', 'Notebook'],
            ['computacion/computadores/notebooks-gamers', 'Notebook'],
            ['computacion/computadores/computacion-apple', 'Notebook'],
            ['tv-audio/tv/led', 'Television'],
            ['tv-audio/tv/oled-uhd-y-suhd', 'Television'],
            ['computacion/tablets/android-y-windows', 'Tablet'],
            ['computacion/tablets/ipad', 'Tablet'],
            ['electrohogar/refrigeracion/refrigeradores', 'Refrigerator'],
            ['electrohogar/refrigeracion/freezer', 'Refrigerator'],
            ['electrohogar/refrigeracion/frigobar', 'Refrigerator'],
            # ['electrohogar/refrigeracion/cavas-de-vinos', 'Refrigerator'],
            ['computacion/impresoras-y-tintas/multifuncionales', 'Printer'],
            ['computacion/impresoras-y-tintas/impresoras-a-tinta', 'Printer'],
            ['computacion/impresoras-y-tintas/impresoras-laser', 'Printer'],
            ['computacion/impresoras-y-tintas/multifuncionales-e-impresoras',
             'Printer'],
            ['electrohogar/cocina/microondas', 'Oven'],
            ['electrohogar/cocina/hornos-empotrados', 'Oven'],
            ['electrohogar/cocina/hornos-electricos', 'Oven'],
            ['electrohogar/electrodomesticos/aspiradoras-y-enceradoras',
             'VacuumCleaner'],
            ['electrohogar/lavado-y-secado/lavadoras', 'WashingMachine'],
            ['electrohogar/lavado-y-secado/secadoras', 'WashingMachine'],
            ['electrohogar/lavado-y-secado/lavadoras-secadoras',
             'WashingMachine'],
            ['telefonia/celulares/smartphones', 'Cell'],
            ['telefonia/celulares/iphone', 'Cell'],
            ['telefonia/celulares/basicos', 'Cell'],
            ['entretenimiento/fotografia/camaras-semi-profesionales',
             'Camera'],
            ['entretenimiento/fotografia/camaras-compactas', 'Camera'],
            ['tv-audio/audio/equipos-de-musica', 'StereoSystem'],
            ['tv-audio/audio/hi-fi', 'StereoSystem'],
            ['telefonia/accesorios-telefonia/parlantes-portatiles',
             'StereoSystem'],
            ['tv-audio/reproductores-y-accesorios/blu-ray-y-dvd',
             'OpticalDiskPlayer'],
            ['tv-audio/audio/home-cine', 'HomeTheater'],
            ['computacion/almacenamiento/discos-duros',
             'ExternalStorageDrive'],
            ['computacion/almacenamiento/pendrives', 'UsbFlashDrive'],
            ['telefonia/accesorios-telefonia/memorias', 'MemoryCard'],
            ['computacion/proyectores-y-monitores/proyectores', 'Projector'],
            ['entretenimiento/videojuegos/consolas', 'VideoGameConsole'],
            ['computacion/proyectores-y-monitores/monitores', 'Monitor'],
            ['computacion/computadores/pc-all-in-one', 'AllInOne'],
            ['electrohogar/climatizacion/ventilacion-y-aire-acondicionado',
             'AirConditioner'],
            ['electrohogar/bano/calefont-y-termos', 'WaterHeater'],
            ['electrohogar/climatizacion/estufas', 'SpaceHeater'],
            ['telefonia/smartwatches-and-wearables', 'Smartwatch'],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            print(category_path)

            page = 1

            while True:
                if page > 30:
                    raise Exception('Page overflow')

                page_url = url_base.format(category_path, page)
                soup = BeautifulSoup(session.get(page_url).text, 'html.parser')

                product_link_containers = soup.find(
                    'div', 'catalog-container')

                if not product_link_containers:
                    if page == 1:
                        print(page_url)
                        raise Exception('Empty category path: {} - {}'.format(
                            category, category_path))
                    else:
                        break

                product_link_containers = product_link_containers.findAll(
                    'a', 'catalog-item')

                for link_tag in product_link_containers:
                    product_url = 'https://simple.ripley.cl' + link_tag['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        product_data = re.search(r'window.__PRELOADED_STATE__ = (.+);',
                                 page_source)
        product_json = json.loads(product_data.groups()[0])
        specs_json = product_json['product']['product']

        sku = specs_json['partNumber']
        if specs_json['isOutOfStock'] or specs_json['isUnavailable']:
            stock = 0
        else:
            stock = specs_json['xCatEntryQuantity']

        if 'offerPrice' in specs_json['prices']:
            normal_price = Decimal(specs_json['prices']['offerPrice'])
        elif 'listPrice' in specs_json['prices']:
            normal_price = Decimal(specs_json['prices']['listPrice'])
        else:
            return []

        offer_price = Decimal(specs_json['prices'].get('cardPrice',
                                                       normal_price))

        description = ''

        if 'longDescription' in specs_json:
            description += html_to_markdown(specs_json['longDescription'])

        description += '\n\nAtributo | Valor\n-- | --\n'

        for attribute in specs_json['attributes']:
            description += '{} | {}\n'.format(attribute['name'],
                                              attribute['value'])

        description += '\n\n'

        picture_urls = []
        for path in specs_json['images']:
            picture_url = path

            if not picture_url.startswith('https'):
                picture_url = 'https:' + picture_url

            picture_urls.append(picture_url)

        p = Product(
            specs_json['name'],
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
            cell_plan_name=None,
            cell_monthly_payment=None,
            picture_urls=picture_urls
        )

        return [p]
