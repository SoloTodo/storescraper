import json
import re

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, \
    session_with_proxy


class PcFactory(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'VideoCard',
            'Processor',
            'Monitor',
            'Television',
            'Motherboard',
            'Ram',
            'StorageDrive',
            'SolidStateDrive',
            'PowerSupply',
            'ComputerCase',
            'CpuCooler',
            'Tablet',
            'Printer',
            'Cell',
            'Camera',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Projector',
            'VideoGameConsole',
            'StereoSystem',
            'AllInOne',
            'Mouse',
            'OpticalDrive',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'Wearable',
            'Ups',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['735', ['Notebook'],
             'Inicio > Computadores y Tablets > Notebooks', 1],
            ['334', ['VideoCard'],
             'Inicio > Componentes/Partes y Piezas > Tarjetas Gráficas > '
             'Tarjetas Gráficas AMD', 1],
            ['994', ['Tablet'],
             'Inicio > Computadores y Tablets > Tablets', 1],
            ['432', ['Cell'],
             'Inicio > Celulares > Smartphones', 1],
            ['6', ['Camera'],
             'Inicio > Fotografía, Video y Drones > Cámaras Compactas', 1],
            ['620', ['Camera'],
             'Inicio > Fotografía, Video y Drones > '
             'Cámaras Semiprofesionales', 1],
            ['422', ['ExternalStorageDrive'],
             'Inicio > Discos Duros y Almacenamiento > Discos Externos', 1],
            ['904', ['ExternalStorageDrive'],
             'Inicio > Discos Duros y Almacenamiento > SSD Externos ', 1],
            ['218', ['UsbFlashDrive'],
             'Inicio > Discos Duros y Almacenamiento > Pendrives', 1],
            ['48', ['MemoryCard'],
             'Inicio > Discos Duros y Almacenamiento > Memoris Flash', 1],
            ['46', ['Projector'],
             'Inicio > Monitores y Proyectores > Proyectores', 1],
            ['438', ['VideoGameConsole'],
             'Inicio > Juegos y Consola > Consolas', 1],
            ['889', ['StereoSystem'],
             'Inicio > Audio > Equipos de Música', 1],
            ['890', ['StereoSystem'],
             'Inicio > Audio > Equipos de Música > Audio All in One', 1],
            ['798', ['StereoSystem'],
             'Inicio > Audio > Equipos de Música > Microcomponente', 1],
            ['700', ['StereoSystem'],
             'Inicio > Audio > Equipos de Música > Minicomponentes', 1],
            ['831', ['StereoSystem'],
             'Inicio > Audio > Parlantes > Parlantes PC', 1],
            ['34', ['StereoSystem'],
             'Inicio > Audio > Parlantes > Parlantes Portátiles', 1],
            ['797', ['StereoSystem'],
             'Inicio > TV y Smart TV > Video/Audio TV > Barras de Sonido', 1],
            ['475', ['AllInOne'],
             'Inicio > Computadores y Tablets > Escritorio > All-in-One', 1],
            ['22', ['Mouse'],
             'Inicio > Computadores y Tablets > Mouses y Teclados > '
             'Mouses', 1],
            ['789', ['Television'],
             'Inicio > TV y Smart TV > TV y Smart TV', 1],
            ['286', ['OpticalDrive'],
             'Inicio > Componentes/Partes y Piezas > Ópticos', 1],
            ['272', ['Processor'],
             'Inicio > Componentes/Partes y Piezas > Procesadores', 1],
            ['995', ['Monitor'],
             'Inicio > Monitores y Proyectores > Monitores', 1],
            ['292', ['Motherboard'],
             'Inicio > Componentes/Partes y Piezas > Placas Madres', 1],
            ['112', ['Ram'],
             'Inicio > Componentes/Partes y Piezas > Memorias > '
             'Memorias PC', 1],
            ['100', ['Ram'],
             'Inicio > Componentes/Partes y Piezas > Memorias > '
             'Memorias Notebook', 1],
            ['266', ['Ram'],
             'Inicio > Computadores y Tablets > Servidores > '
             'Memorias Servers', 1],
            ['340', ['StorageDrive'],
             'Inicio > Discos Duros y Almacenamiento > Discos Duros PC', 1],
            ['585', ['SolidStateDrive'],
             'Inicio > Discos Duros y Almacenamiento > Discos SSD', 1],
            ['421', ['StorageDrive'],
             'Inicio > Discos Duros y Almacenamiento > Discos Notebooks', 1],
            ['932', ['StorageDrive'],
             'Inicio > Discos Duros y Almacenamiento > '
             'Discos de Video Vigilancia', 1],
            ['54', ['PowerSupply'],
             'Inicio > Componentes/Partes y Piezas > '
             'Fuentes de Poder (PSU)', 1],
            ['16', ['ComputerCase'],
             'Inicio > Componentes/Partes y Piezas > Gabinetes > '
             'Gabinetes con Fuente', 1],
            ['328', ['ComputerCase'],
             'Inicio > Componentes/Partes y Piezas > Gabinetes > '
             'Gabinetes sin Fuente', 1],
            ['42', ['CpuCooler'],
             'Inicio > Componentes/Partes y Piezas > Refrigeración', 1],
            ['262', ['Printer'],
             'Inicio > Impresoras y Suministros > '
             'Impresoras Hogar y Oficina', 1],
            ['36', ['Keyboard'],
             'Inicio > Computadores y Tablets > Mouse y Teclados > '
             'Teclados', 1],
            ['418', ['KeyboardMouseCombo'],
             'Inicio > Computadores y Tablets > Mouses y Teclados > '
             'Combos Teclado/Mouse', 1],
            ['850', ['Headphones'],
             'Inicio > Audio > Audifonos', 1],
            ['860', ['Headphones'],
             'Inicio > Audio > Audifonos > Audifonos DJ', 1],
            ['861', ['Headphones'],
             'Inicio > Audio > Audifonos > Audifonos Monitoreo', 1],
            ['685', ['Wearable'],
             'Inicio > Celulares > Wearables > Smartwatches', 1],
            ['38', ['Ups'],
             'Inicio > Accesorios y Periféricos > UPS y Energía > '
             'UPS y Reguladores', 1],
            ['748', ['StereoSystem'],
             'Inicio > Smart Home (Domótica)', 1]
        ]

        session = session_with_proxy(extra_args)
        session.get('https://www.pcfactory.cl')

        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 1
            current_position = 1

            while True:
                if page > 30:
                    raise Exception('Page overflow')

                category_url = 'https://www.pcfactory.cl/foo?categoria={}' \
                               '&pagina={}'.format(category_path, page)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                if not soup.find('div', 'titulo_categoria'):
                    raise Exception('Invalid category:' + category_url)

                product_cells = soup.findAll('div', 'wrap-caluga-matrix')

                if not product_cells:
                    if page == 1:
                        raise Exception('Empty category path: {}'.format(
                            category_url))
                    else:
                        break

                for product_cell in product_cells:
                    sku = product_cell.find('span', 'txt-id').text.strip()
                    product_url = 'https://www.pcfactory.cl/producto/{}' \
                                  ''.format(sku)
                    product_entries[product_url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': current_position
                    })

                    current_position += 1

                page += 1

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        for i in range(10):
            session.get(url)

            response = session.get(
                'https://www.pcfactory.cl/public/scripts/dynamic/initData'
                '.js?_={}'.format(datetime.now().timestamp()))

            raw_json = re.search(
                r'window.pcFactory.dataGlobal.serverData			=  (.+)',
                response.text).groups()[0][:-1]

            response_data = json.loads(raw_json)
            if 'producto' in response_data:
                break
        else:
            raise Exception('Too many retries')

        product_data = response_data['producto']

        if not product_data:
            return []

        full_name = '{} {}'.format(product_data['marca'],
                                   product_data['nombre'])

        stock = int(product_data['stock_tienda']) + \
            int(product_data['stock_web'])
        sku = product_data['id_producto']
        description = product_data['descripcion']

        if description:
            description = html_to_markdown(description)

        picture_urls = ['https://www.pcfactory.cl/public/foto/{}/{}'.format(
            sku, path) for path in product_data['imagen']]

        p = Product(
            full_name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            Decimal(remove_words(product_data['precio_normal'])),
            Decimal(remove_words(product_data['precio_cash'])),
            'CLP',
            sku=sku,
            part_number=product_data['partno'],
            description=description,
            picture_urls=picture_urls
        )

        return [p]
