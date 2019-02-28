import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.banner_sections import *


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
            'Wearable',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://simple.ripley.cl/{}?page={}'

        category_urls = [
            ['tecno/computacion/notebooks', 'Notebook'],
            # ['tecno/computacion/2-en-1convertibles', 'Notebook'],
            ['tecno/computacion/notebooks-gamer', 'Notebook'],
            ['computacion/computadores/notebooks-gamers', 'Notebook'],
            ['tecno/computacion/tablets-y-tabletas-de-disenos', 'Tablet'],
            ['tecno/computacion/impresoras-y-tintas', 'Printer'],
            ['tecno/computacion/almacenamiento', 'UsbFlashDrive'],
            ['tecno/computacion/pc-all-in-one', 'AllInOne'],
            ['tecno/computacion/proyectores-y-monitores', 'Monitor'],
            ['mercado-ripley/gamer', 'Mouse'],
            ['tecno/television/smart-tv', 'Television'],
            ['tecno/television/basicos', 'Television'],
            ['tecno/television/oled-suhd-y-qled', 'Television'],
            ['tecno/television/ultra-hd-y-4k', 'Television'],
            ['tecno/television/full-hd', 'Television'],
            ['tecno/television/hd', 'Television'],
            ['electro/refrigeracion/refrigeradores', 'Refrigerator'],
            ['electro/refrigeracion/frigobar', 'Refrigerator'],
            ['electro/cocina/microondas', 'Oven'],
            ['electro/cocina/hornos', 'Oven'],
            ['electro/aseo', 'VacuumCleaner'],
            ['electro/lavanderia/lavadoras', 'WashingMachine'],
            ['electro/lavanderia/secadoras', 'WashingMachine'],
            ['electro/lavanderia/lavadora-secadora', 'WashingMachine'],
            ['electro/lavanderia/doble-carga', 'WashingMachine'],
            ['telefonia/celulares/smartphones', 'Cell'],
            ['tecno/telefonia/smartphones', 'Cell'],
            # ['telefonia/celulares/iphone', 'Cell'],
            # ['telefonia/celulares/basicos', 'Cell'],
            # ['tecno/telefonia/basicos', 'Cell'],
            ['tecno/fotografia-y-video/semi-profesionales',
             'Camera'],
            ['entretenimiento/fotografia/camaras-compactas', 'Camera'],
            # ['tecno/audio-y-musica/hi-fi', 'StereoSystem'],
            ['tecno/audio-y-musica/parlantes-y-subwoofer', 'StereoSystem'],
            ['tecno/audio-y-musica/microcomponentes', 'StereoSystem'],
            ['tecno/audio-y-musica/home-cinema', 'StereoSystem'],
            ['tecno/audio-y-musica/audio-portable', 'StereoSystem'],
            ['tv-audio/audio/hi-fi', 'StereoSystem'],
            ['tv-audio/audio/tornamesas', 'StereoSystem'],
            ['tv-audio/audio/radios-y-grabadoras', 'StereoSystem'],
            ['tecno/television/bluray', 'OpticalDiskPlayer'],
            ['tecno/television/dvd-y-tv-portatil', 'OpticalDiskPlayer'],
            ['telefonia/accesorios-telefonia/memorias', 'MemoryCard'],
            ['tecno/videojuegos/consolas', 'VideoGameConsole'],
            ['electro/climatizacion/ventiladores-y-aire-acondicionado',
             'AirConditioner'],
            ['electro/climatizacion/estufas-y-calefactores', 'SpaceHeater'],
            ['telefonia/smartwatches-and-wearables/smartwatch', 'Wearable'],
            ['tecno/audio-y-musica/audifonos', 'Headphones'],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 40:
                    raise Exception('Page overflow')

                page_url = url_base.format(category_path, page)
                print(page_url)
                soup = BeautifulSoup(session.get(page_url).text, 'html.parser')

                product_link_containers = soup.find(
                    'div', 'catalog-container')

                if not product_link_containers:
                    if page == 1:
                        raise Exception('Empty category path: {} - {}'.format(
                            category, category_path))
                    else:
                        break

                product_link_containers = product_link_containers.findAll(
                    'a', 'catalog-product-item')

                if not product_link_containers:
                    raise Exception('Category error: ' + category_path)

                for link_tag in product_link_containers:
                    product_url = 'https://simple.ripley.cl' + link_tag['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text

        soup = BeautifulSoup(page_source, 'html.parser')

        if soup.find('div', 'error-page'):
            return []

        product_data = re.search(r'window.__PRELOADED_STATE__ = (.+);',
                                 page_source)
        product_json = json.loads(product_data.groups()[0])
        specs_json = product_json['product']['product']

        sku = specs_json['partNumber']
        if specs_json['isOutOfStock'] or specs_json['isUnavailable']:
            stock = 0
        else:
            stock = -1

        if 'offerPrice' in specs_json['prices']:
            normal_price = Decimal(specs_json['prices']['offerPrice'])
        elif 'listPrice' in specs_json['prices']:
            normal_price = Decimal(specs_json['prices']['listPrice'])
        else:
            return []

        offer_price = Decimal(specs_json['prices'].get('cardPrice',
                                                       normal_price))

        if offer_price > normal_price:
            offer_price = normal_price

        description = ''

        if 'longDescription' in specs_json:
            description += html_to_markdown(specs_json['longDescription'])

        description += '\n\nAtributo | Valor\n-- | --\n'

        for attribute in specs_json['attributes']:
            if 'name' in attribute and 'value' in attribute:
                description += '{} | {}\n'.format(attribute['name'],
                                                  attribute['value'])

        description += '\n\n'

        picture_urls = []
        for path in specs_json['images']:
            picture_url = path

            if picture_url.startswith('file://'):
                continue

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
            picture_urls=picture_urls
        )

        return [p]

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://simple.ripley.cl/{}'

        sections_data = [
            [HOME, 'Home', SUBSECTION_TYPE_HOME, ''],
            [ELECTRO_RIPLEY, 'Electro Ripley',
             SUBSECTION_TYPE_CATEGORY_PAGE, 'electro/'],
            [TECNO_RIPLEY, 'Tecno Ripley',
             SUBSECTION_TYPE_CATEGORY_PAGE, 'tecno/'],
            [REFRIGERATION, 'Refrigeración',
             SUBSECTION_TYPE_MOSAIC, 'electro/refrigeracion/'],
            [REFRIGERATION, 'Refrigeradores',
             SUBSECTION_TYPE_MOSAIC, 'electro/refrigeracion/refrigeradores/'],
            [WASHING_MACHINES, 'Lavandería',
             SUBSECTION_TYPE_MOSAIC, 'electro/lavanderia'],
            [WASHING_MACHINES, 'Lavadoras',
             SUBSECTION_TYPE_MOSAIC, 'electro/lavanderia/lavadoras'],
            [WASHING_MACHINES, 'Lavadora-secadora',
             SUBSECTION_TYPE_MOSAIC, 'electro/lavanderia/lavadora-secadora'],
            [WASHING_MACHINES, 'Doble Carga',
             SUBSECTION_TYPE_MOSAIC, 'electro/lavanderia/doble-carga'],
            [TELEVISIONS, 'Televisión',
             SUBSECTION_TYPE_MOSAIC, 'tecno/television'],
            [TELEVISIONS, 'Smart TV',
             SUBSECTION_TYPE_MOSAIC, 'tecno/television/smart-tv'],
            [TELEVISIONS, 'OLED, SUHD, y QLED',
             SUBSECTION_TYPE_MOSAIC, 'tecno/television/oled-suhd-y-qled'],
            [TELEVISIONS, 'Ultra HD y 4K',
             SUBSECTION_TYPE_MOSAIC, 'tecno/television/ultra-hd-y-4k'],
            [TELEVISIONS, 'Full HD',
             SUBSECTION_TYPE_MOSAIC, 'tecno/television/full-hd'],
            [AUDIO, 'Audio y Música',
             SUBSECTION_TYPE_MOSAIC, 'tecno/audio-y-musica'],
            [AUDIO, 'Parlantes y Subwoofer', SUBSECTION_TYPE_MOSAIC,
             'tecno/audio-y-musica/parlantes-y-subwoofer'],
            [AUDIO, 'Microcomponentes',
             SUBSECTION_TYPE_MOSAIC, 'tecno/audio-y-musica/microcomponentes'],
            [AUDIO, 'Home Cinema',
             SUBSECTION_TYPE_MOSAIC, 'tecno/audio-y-musica/home-cinema'],
            [AUDIO, 'Audio Portable',
             SUBSECTION_TYPE_MOSAIC, 'tecno/audio-y-musica/audio-portable'],
            [CELLS, 'Telefonía',
             SUBSECTION_TYPE_MOSAIC, 'tecno/telefonia'],
            [CELLS, 'Smartphones',
             SUBSECTION_TYPE_MOSAIC, 'tecno/telefonia/smartphones']
        ]

        session = session_with_proxy(extra_args)
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            if subsection_type == SUBSECTION_TYPE_HOME:
                images = soup.find('div', 'carousel js-home-carousel') \
                    .findAll('span', 'bg-item huincha-desktop')

                for index, image in enumerate(images):
                    picture_url = re.search(r'url\((.*?)\)', image['style']) \
                        .group(1)
                    banners.append({
                        'url': url,
                        'picture_url': picture_url,
                        'key': picture_url,
                        'position': index + 1,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type
                    })
            elif subsection_type == SUBSECTION_TYPE_CATEGORY_PAGE:
                images = soup.findAll('a', 'item')

                for index, image in enumerate(images):
                    picture = image.find('span', 'bg-item')
                    picture_url = re.search(r'url\((.*?)\)', picture['style'])\
                        .group(1)
                    banners.append({
                        'url': url,
                        'picture_url': picture_url,
                        'key': picture_url,
                        'position': index + 1,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type
                    })
            elif subsection_type == SUBSECTION_TYPE_MOSAIC:
                picture_url = soup.find('section', 'catalog-top-banner')\
                    .find('img')

                if not picture_url:
                    continue

                banners.append({
                    'url': url,
                    'picture_url': picture_url['src'],
                    'key': picture_url['src'],
                    'position': 1,
                    'section': section,
                    'subsection': subsection,
                    'type': subsection_type
                })
            else:
                raise Exception('Invalid subsection type')

        return banners
