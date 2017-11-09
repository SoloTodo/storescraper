import json
import urllib

import re
from datetime import datetime
from decimal import Decimal

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
            ['34', '268', 'StereoSystem'],
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
            ['246', '262', 'Printer'],  # Impresoras Laser
            ['18', '262', 'Printer'],  # Impresoras Tinta
            ['236', '262', 'Printer'],  # Imp. Multifuncionales
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

                service_navegacion_data = {
                    'navegacion': {
                        'busqueda': '',
                        'categoria': categoria,
                        'id_sucursal': -1,
                        'inicial': (page - 1) * step,
                        'termino': page * step,
                        'maxItemsPorPagina': step,
                        'orden': 0,
                        'pag_fin': 6,
                        'pag_ini': 1,
                        'papa': papa,
                        'tabulaciones': [],
                        'tiendas': [
                            {'childs': [
                                {'id_sucursal': -1,
                                 'seleccionada': True,
                                 'sucursal': 'Todas'},
                                {'id_sucursal': '11',
                                 'seleccionada': None,
                                 'sucursal': 'Internet'},
                                {'id_sucursal': '31',
                                 'seleccionada': None,
                                 'sucursal': 'Mall Plaza Calama'},
                                {'id_sucursal': '24',
                                 'seleccionada': None,
                                 'sucursal': 'Antofagasta'},
                                {'id_sucursal': '27',
                                 'seleccionada': None,
                                 'sucursal': 'Copiap\xf3'},
                                {'id_sucursal': '8',
                                 'seleccionada': None,
                                 'sucursal': 'La Serena'},
                                {'id_sucursal': '5',
                                 'seleccionada': None,
                                 'sucursal': 'Vi\xf1a del Mar'},
                                {'id_sucursal': '28',
                                 'seleccionada': None,
                                 'sucursal': 'Ahumada'},
                                {'id_sucursal': '21',
                                 'seleccionada': None,
                                 'sucursal': 'Agustinas'},
                                {'id_sucursal': '6',
                                 'seleccionada': None,
                                 'sucursal': 'Las Condes'},
                                {'id_sucursal': '16',
                                 'seleccionada': None,
                                 'sucursal': 'Los Leones'},
                                {'id_sucursal': '2',
                                 'seleccionada': None,
                                 'sucursal': 'Manuel Montt'},
                                {'id_sucursal': '30',
                                 'seleccionada': None,
                                 'sucursal': 'Mall Arauco Maip\xfa'},
                                {'id_sucursal': '22',
                                 'seleccionada': None,
                                 'sucursal': 'Mall Costanera Center'},
                                {'id_sucursal': '10',
                                 'seleccionada': None,
                                 'sucursal': 'Mall Plaza Alameda'},
                                {'id_sucursal': '17',
                                 'seleccionada': None,
                                 'sucursal': 'Mall Plaza Norte'},
                                {'id_sucursal': '9',
                                 'seleccionada': None,
                                 'sucursal': 'Mall Plaza Oeste'},
                                {'id_sucursal': '3',
                                 'seleccionada': None,
                                 'sucursal': 'Mall Plaza Vespucio'},
                                {'id_sucursal': '33',
                                 'seleccionada': None,
                                 'sucursal': 'Puente Alto'},
                                {'id_sucursal': '18',
                                 'seleccionada': None,
                                 'sucursal': 'Rancagua'},
                                {'id_sucursal': '34',
                                 'seleccionada': None,
                                 'sucursal': 'Curico'},
                                {'id_sucursal': '20',
                                 'seleccionada': None,
                                 'sucursal': 'Talca'},
                                {'id_sucursal': '26',
                                 'seleccionada': None,
                                 'sucursal': 'Chillan'},
                                {'id_sucursal': '32',
                                 'seleccionada': None,
                                 'sucursal': 'Mall Plaza Tr\xe9bol'},
                                {'id_sucursal': '7',
                                 'seleccionada': None,
                                 'sucursal': 'Concepci\xf3n'},
                                {'id_sucursal': '25',
                                 'seleccionada': None,
                                 'sucursal': 'Los \xc1ngeles'},
                                {'id_sucursal': '14',
                                 'seleccionada': None,
                                 'sucursal': 'Temuco'},
                                {'id_sucursal': '29',
                                 'seleccionada': None,
                                 'sucursal': 'Osorno'},
                                {'id_sucursal': '19',
                                 'seleccionada': None,
                                 'sucursal': 'Puerto Montt'}],
                                'name': 'Filtro por Tienda',
                                'state': 'collapsed'}],
                        'tipoVistaCaluga': 'matrix',
                        'total_regs': 108,
                        'url_parameters': {'categoria': '425',
                                           'papa': '735'}},
                    'requestableController': 'ServiceNavegacion',
                    'requestableOperation': 'setNavegacion',
                    'requestableType': 'REQUESTABLE_TYPE_CONTROLLER'}

                session.post(
                    'https://www.pcfactory.cl/services/ServiceNavegacion',
                    'data={}'.format(urllib.parse.quote(json.dumps(
                        service_navegacion_data, separators=(',', ':')))))

                cookie = session.cookies['PHPSESSID']

                response = session.post(
                    'https://www.pcfactory.cl/services/productos/'
                    'ServiceProducto',
                    data='data=%7B%22requestableOperation%22%3A%22producto'
                         'CategoriaList%22%2C%22requestableType%22%3A%22'
                         'REQUESTABLE_TYPE_CONTROLLER%22%2C%22requestable'
                         'Controller%22%3A%22ServiceProducto%22%7D',
                    headers={
                        'Cookie': 'PHPSESSID={}'.format(cookie),
                        'User-Agent': 'User-Agent: Mozilla/5.0 (X11; '
                                      'Linux x86_64) AppleWebKit/537.36 ('
                                      'KHTML, like Gecko) Chrome/'
                                      '59.0.3071.115 Safari/537.36'
                    },
                )

                products_info = json.loads(response.text)

                if not products_info['data']:
                    if page == 1:
                        raise Exception('Empty category path: {} - {}'.format(
                            category, categoria))
                    else:
                        break

                for product_entry in products_info['data']:
                    stock = int(product_entry['stock_tienda']) + int(
                        product_entry['stock_web'])
                    if not stock:
                        continue

                    product_url = 'https://www.pcfactory.cl/producto/{}' \
                                  ''.format(product_entry['id_producto'])
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
