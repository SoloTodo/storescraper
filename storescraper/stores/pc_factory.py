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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        step = 100

        url_extensions = [
            ['425', '735', 'Notebook'],  # Notebooks
            ['426', '735', 'Notebook'],  # Convertibles
            ['659', '735', 'Notebook'],  # Ultralivianos
            ['454', '334', 'VideoCard'],  # Tarjetas de video AMD
            ['378', '334', 'VideoCard'],  # Tarjetas de video NVIDIA
            ['488', '735', 'Tablet'],  # Tablets
            ['432', '645', 'Cell'],  # Celulares
            ['6', '643', 'Camera'],  # Camaras compactas
            ['620', '643', 'Camera'],  # Camaras semiprofesional
            ['422', '706', 'ExternalStorageDrive'],
            ['218', '706', 'UsbFlashDrive'],
            ['48', '264', 'MemoryCard'],
            ['46', '256', 'Projector'],
            ['438', '374', 'VideoGameConsole'],
            # ['34', '891', 'StereoSystem'],
            ['889', '268', 'StereoSystem'],
            ['475', '737', 'AllInOne'],
            ['22', '304', 'Mouse'],
            ['789', '788', 'Television'],
            ['286', '633', 'OpticalDrive'],
            ['272', '272', 'Processor'],  # Procesadores
            ['250', '256', 'Monitor'],  # Monitores LCD
            ['292', '292', 'Motherboard'],  # Placas madre
            ['112', '264', 'Ram'],  # Memoria PC
            ['100', '264', 'Ram'],  # Memoria Notebook
            ['340', '312', 'StorageDrive'],  # HDD PC
            ['585', '312', 'SolidStateDrive'],  # SSD
            ['421', '312', 'StorageDrive'],  # HDD Notebook
            ['54', '326', 'PowerSupply'],  # Fuentes de poder
            ['16', '326', 'ComputerCase'],  # Gabinetes con PSU
            ['328', '326', 'ComputerCase'],  # Gabinetes sin PSU
            ['42', '300', 'CpuCooler'],  # Refrigeracion
            ['262', '262', 'Printer'],  # Impresoras Laser
        ]

        session = session_with_proxy(extra_args)
        session.get('https://www.pcfactory.cl')

        product_urls = []
        for categoria, papa, extension_category in url_extensions:
            if extension_category != category:
                continue

            page = 1

            while True:
                if page > 30:
                    raise Exception('Page overflow')

                category_url = 'https://www.pcfactory.cl/?categoria={}' \
                               '&pagina={}'.format(categoria, page)
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

        session.get(url)

        response = session.get(
            'https://www.pcfactory.cl/public/scripts/dynamic/initData.js?_={}'
            ''.format(datetime.now().timestamp()),
            )

        raw_json = re.search(
            r'window.pcFactory.dataGlobal.serverData			=  (.+)',
            response.text).groups()[0][:-1]

        response_data = json.loads(raw_json)
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
