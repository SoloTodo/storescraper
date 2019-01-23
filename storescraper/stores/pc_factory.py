import json
import urllib

import re
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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['735', 'Notebook'],  # Notebooks
            ['454', 'VideoCard'],  # Tarjetas de video AMD
            ['378', 'VideoCard'],  # Tarjetas de video NVIDIA
            ['488', 'Tablet'],  # Tablets
            ['432', 'Cell'],  # Celulares
            ['6', 'Camera'],  # Camaras compactas
            ['620', 'Camera'],  # Camaras semiprofesional
            ['422', 'ExternalStorageDrive'],
            ['218', 'UsbFlashDrive'],
            ['48', 'MemoryCard'],
            ['46', 'Projector'],
            ['438', 'VideoGameConsole'],
            ['889', 'StereoSystem'],  # Equipos de Música
            ['890', 'StereoSystem'],  # Audio All in One
            ['798', 'StereoSystem'],  # Microcomponentes
            ['700', 'StereoSystem'],  # Minicomponentes
            ['831', 'StereoSystem'],  # Parlantes PC
            ['34', 'StereoSystem'],  # Parlantes Portátiles
            ['797', 'StereoSystem'],  # Barras de Sonido
            ['475', 'AllInOne'],
            ['22', 'Mouse'],
            ['789', 'Television'],
            ['286', 'OpticalDrive'],
            ['272', 'Processor'],  # Procesadores
            ['250', 'Monitor'],  # Monitores LCD
            ['292', 'Motherboard'],  # Placas madre
            ['112', 'Ram'],  # Memoria PC
            ['100', 'Ram'],  # Memoria Notebook
            ['340', 'StorageDrive'],  # HDD PC
            ['585', 'SolidStateDrive'],  # SSD
            ['421', 'StorageDrive'],  # HDD Notebook
            ['54', 'PowerSupply'],  # Fuentes de poder
            ['16', 'ComputerCase'],  # Gabinetes con PSU
            ['328', 'ComputerCase'],  # Gabinetes sin PSU
            ['42', 'CpuCooler'],  # Refrigeracion
            ['262', 'Printer'],  # Impresoras Laser
            ['36', 'Keyboard'],  # Teclados
            ['418', 'KeyboardMouseCombo'],  # Combo teclado mouse
            ['850', 'Headphones'],  # Audifonos
            ['895', 'Headphones'],  # Audifonos
            ['860', 'Headphones'],  # Audífonos DJ
            ['861', 'Headphones'],  # Audífonos Monitoreo
            ['685', 'Wearable']
        ]

        session = session_with_proxy(extra_args)
        session.get('https://www.pcfactory.cl')

        product_urls = []
        for categoria, extension_category in url_extensions:
            if extension_category != category:
                continue

            page = 1

            while True:
                if page > 30:
                    raise Exception('Page overflow')

                category_url = 'https://www.pcfactory.cl/foo?categoria={}' \
                               '&pagina={}'.format(categoria, page)
                print(category_url)
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
                    product_urls.append(product_url)

                page += 1

        return product_urls

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
        description = html_to_markdown(product_data['descripcion'])

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
