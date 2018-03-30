import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


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
            ['tecnologia/computadores/todo_notebooks', 'Notebook'],
            ['electronica/televisores/led2', 'Television'],
            ['electronica/televisores/smart_tv', 'Television'],
            ['electronica/televisores/oled_i_qled_i_curvo', 'Television'],
            ['electronica/televisores/dvd_i_blu_ray', 'OpticalDiskPlayer'],
            ['tecnologia/computadores/tablet', 'Tablet'],
            ['linea_blanca/refrigeradores/side_by_side', 'Refrigerator'],
            ['linea_blanca/refrigeradores/no_frost', 'Refrigerator'],
            ['linea_blanca/refrigeradores/frio_directo', 'Refrigerator'],
            ['linea_blanca/refrigeradores/frigobar', 'Refrigerator'],
            ['linea_blanca/refrigeradores/freezer', 'Refrigerator'],
            ['tecnologia/impresoras/impresoras_laser', 'Printer'],
            ['tecnologia/impresoras/impresoras_a_tinta', 'Printer'],
            ['tecnologia/impresoras/multifuncionales', 'Printer'],
            ['electronica/celulares/smartphones', 'Cell'],
            ['electronica/celulares/telefonos_basicos', 'Cell'],
            ['electronica/audio/equipos_de_musica', 'StereoSystem'],
            ['electronica/audio/home_theater', 'HomeTheater'],
            ['electronica/videojuegos/todo_consolas', 'VideoGameConsole'],
            ['tecnologia/accesorios_computacion/disco_duro_externo',
             'ExternalStorageDrive'],
            ['tecnologia/accesorios_computacion/proyectores', 'Projector'],
            ['tecnologia/accesorios_computacion/pendrives',
             'UsbFlashDrive'],
            ['linea_blanca/lavado_secado/lavadoras', 'WashingMachine'],
            ['linea_blanca/lavado_secado/lavadoras___secadoras',
             'WashingMachine'],
            ['linea_blanca/lavado_secado/secadoras', 'WashingMachine'],
            ['linea_blanca/lavado_secado/centrifugas', 'WashingMachine'],
            ['linea_blanca/climatizacion/calefont', 'WaterHeater'],
            # ['linea_blanca/climatizacion/enfriadores', 'AirConditioner'],
            ['linea_blanca/climatizacion/estufas_a_parafina', 'SpaceHeater'],
            ['linea_blanca/climatizacion/estufas_electricas', 'SpaceHeater'],
            ['linea_blanca/cocina/microondas', 'Oven'],
            ['linea_blanca/cocina/hornos_electricos', 'Oven'],
            ['linea_blanca/electrodomesticos/aspiradoras', 'VacuumCleaner'],
            ['tecnologia/accesorios_computacion/otros', 'MemoryCard'],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for extension, local_category in extensions:
            if local_category != category:
                continue

            url = 'https://tienda.lapolar.cl/catalogo/{}?response=' \
                  'json&pageSize=1000'.format(extension)
            print(url)
            products_json = json.loads(session.get(url).text)

            entry_products = products_json['dataset']['products']

            if not entry_products:
                raise Exception('Empty category: ' + url)

            for entry in entry_products:
                product_url = 'https://tienda.lapolar.cl/producto/sku/{}' \
                              ''.format(entry['plu'])
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if not response.ok:
            return []

        page_source = response.text

        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', 'title').text.strip()
        sku = soup.find('span', {'id': 'spanProductPlu'}).text.strip()

        normal_price = Decimal(
            re.search(r'internet: Number\((\d+)\)', page_source).groups()[0])
        offer_price = Decimal(
            re.search(r'laPolarCard: Number\((\d+)\)',
                      page_source).groups()[0])

        available_online = int(
            re.search(r'isAvailableOnline: (\d+),', page_source).groups()[0])

        if available_online:
            stock = -1
        else:
            stock = 0

        if not offer_price:
            offer_price = normal_price

        description = html_to_markdown(
            str(soup.find('div', {'id': 'description'})))

        picture_tags = soup.findAll('img', {'temprop': 'thumbnailUrl'})
        picture_urls = [tag['data-img-large'] for tag in picture_tags]

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
