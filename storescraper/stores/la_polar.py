import json
import re
import requests
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown


class LaPolar(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Monitor',
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
            'AllInOne',
            'AirConditioner',
            'WaterHeater',
            'VideoGameConsole',
            'Projector',
            'SpaceHeater',
            'Smartwatch',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        extensions = [
            ['computacion/notebooks/notebooks2', 'Notebook'],
            ['electronica/tv_video/todos_los_led', 'Television'],
            ['computacion/tablets/tablets2', 'Tablet'],
            ['electrohogar/refrigeracion/todos_los_refrigeradores',
             'Refrigerator'],
            ['computacion/impresoras_multifuncionales/impresoras',
             'Printer'],
            ['electrohogar/cocina/horno_microondas', 'Oven'],
            ['electrohogar/cocina/horno_electrico', 'Oven'],
            ['electrohogar/electrodomesticos/aspiradoras', 'VacuumCleaner'],
            ['electrohogar/lavado_secado/todas_las_lavadoras',
             'WashingMachine'],
            ['electrohogar/lavado_secado/secadoras',
             'WashingMachine'],
            ['electronica/celulares/todos_los_celulares',
             'Cell'],
            ['electronica/camaras_videocamaras/camaras',
             'Camera'],
            ['electronica/audio/microcomponentes',
             'StereoSystem'],
            ['electronica/audio/minicomponentes',
             'StereoSystem'],
            ['electronica/tv_video/reproductores_dvd_blu_ray',
             'OpticalDiskPlayer'],
            ['computacion/almacenamiento/discos_duros_externos',
             'ExternalStorageDrive'],
            ['computacion/almacenamiento/pendrives',
             'UsbFlashDrive'],
            ['electronica/camaras_videocamaras/accesorios',
             'MemoryCard'],
            ['computacion/all_in_one/all_in_one2', 'AllInOne'],
            ['electrohogar/ventilacion/aire_acondicionado_enfriadores',
             'AirConditioner'],
            ['electrohogar/calefaccion/calefont2', 'WaterHeater'],
            ['electronica/consolas_videojuegos/todas_las_consolas',
             'VideoGameConsole'],
            ['electrohogar/calefaccion/todas_las_estufas',
             'SpaceHeater'],
            ['electronica/celulares/smartwatch',
             'Smartwatch'],
        ]

        session = requests.Session()

        product_urls = []

        for extension, local_category in extensions:
            if category != local_category:
                continue
            print(extension)
            url = 'https://www.lapolar.cl/internet/catalogo/' \
                  'todolistados/' + extension

            data = session.get(url).text

            products_json = re.search(
                r'var listado_productos_json = (.+)',
                data).groups()[0][:-1]

            data = json.loads(products_json)

            json_product_array_data = []

            for row in data['lista_completa']:
                json_product_array_data.extend(row['sub_lista'])

            for entry in json_product_array_data:
                sku = entry['ruta'].split('/')[-1]
                product_url = 'https://www.lapolar.cl/internet/catalogo/' \
                              'detalles/busqueda/{}'.format(sku)

                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = requests.Session()
        response = session.get(url, allow_redirects=False)

        if response.status_code != 200:
            return []

        page_source = response.text

        pricing_data = re.search(r'retailrocket.products.post\(([\s\S]*?)\);',
                                 page_source).groups()[0]

        availability_regex = r'"isAvailable": (.+),'

        availability_data = re.search(availability_regex, pricing_data)

        pricing_data = re.sub(availability_regex, '', pricing_data)
        pricing_data = re.sub(r'"categoryPaths": (.+),', '', pricing_data)
        pricing_data = re.sub(r'// .+', '', pricing_data)
        pricing_data = re.sub(
            r'("image_link" : .+),',
            lambda x: str(x.groups()[0]),
            pricing_data)
        pricing_data = pricing_data.replace("\\'", "'")

        pricing_json = json.loads(pricing_data)
        sku = str(pricing_json['id'])
        name = pricing_json['name']
        normal_price = Decimal(pricing_json['price'])
        offer_price = pricing_json['params']['exclusive_price']
        if offer_price:
            offer_price = Decimal(offer_price)
        else:
            offer_price = normal_price

        vendor = pricing_json['vendor']
        model = pricing_json['model']

        product_name = '{} - {} {}'.format(name, vendor, model)

        stock = int(re.match(r'\((-?\d+)',
                             availability_data.groups()[0]).groups()[0])

        soup = BeautifulSoup(page_source, 'html.parser')
        description = html_to_markdown(
            str(soup.find('div', {'id': 'especifica_div'})),
            'https://www.lapolar.cl')

        main_picture_path = soup.find('a', 'imgprincipal')['href']
        picture_urls = ['https://www.lapolar.cl' + main_picture_path]

        thumbs = [path for path in
                  soup.find('div', {'id': 'listaThumbs'}).text.split(';')
                  if path]

        for thumb_part in thumbs:
            if thumb_part == '0':
                continue

            path = thumb_part.split(',')[2]

            if 'alta' in path:
                continue

            path_parts = path.split('/')
            filename = path_parts[-1]
            filename = filename[:1] + 'C' + filename[2:]  # because reasons
            path = '/'.join(path_parts[:-1] + [filename])

            picture_urls.append('https://www.lapolar.cl' + path)

        p = Product(
            product_name,
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
