import json
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import \
    remove_words, session_with_proxy, CF_REQUEST_HEADERS


class FalabellaFast(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 10

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
            'CellAccesory',
            'AllInOne',
            'AirConditioner',
            'Monitor',
            'WaterHeater',
            'SolidStateDrive',
            'Mouse',
            'SpaceHeater',
            'Keyboard',
            'KeyboardMouseCombo',
            'Wearable',
            'Headphones',
            'DishWasher'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        return [category]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        category_paths = [
            ['cat70057', ['Notebook'],
             'Home > Computación-Notebooks', 1],
            # ['cat5860031', ['Notebook'],
            #  'Home > Computación-Notebooks > Notebooks Tradicionales', 1],
            ['cat2028', ['Notebook'],
             'Home > Computación-Notebooks Gamers', 1],
            ['cat2450060', ['Notebook'],
             'Home > Computación-Notebooks > Notebooks Convertibles 2en1', 1],
            # ['cat15880017', ['Notebook'],
            #  'Home > Especiales-Gamer', 1],
            ['cat5860030', ['Notebook'],
             'Home > Computación-Notebooks > MacBooks', 1],
            ['cat4850013', ['Notebook'],
             'Home > Computación-Computación Gamer', 1],
            ['cat1012', ['Television'],
             'Home > Tecnología-TV', 1],
            ['cat7190148', ['Television'],
             'Home > Tecnología-TV > Televisores LED', 1],
            ['cat11161614', ['Television'],
             'Home > Tecnología-TV > LEDs menores a 50 pulgadas', 1],
            ['cat11161675', ['Television'],
             'Home > Tecnología-TV > LEDs entre 50 - 55 pulgadas', 1],
            ['cat11161679', ['Television'],
             'Home > Tecnología-TV > LEDs sobre 55 pulgadas', 1],
            # ['cat2850016', ['Television'],
            #  'Home > TV-Televisores OLED', 1],
            ['cat10020021', ['Television'],
             'Home > TV-Televisores QLED', 1],
            # ['cat18110001', ['Television'],
            #  'Home > Tecnología-Premium', 1],
            ['cat7230007', ['Tablet'],
             'Home > Computación-Tablets', 1],
            ['cat3205', ['Refrigerator'],
             'Home > Refrigeración-Refrigeradores', 1],
            ['cat4074', ['Refrigerator'],
             'Home > Refrigeración-No Frost', 1],
            ['cat4091', ['Refrigerator'],
             'Home > Refrigeración-Side by Side', 1],
            ['cat4036', ['Refrigerator'],
             'Home > Refrigeración-Frío Directo', 1],
            ['cat4048', ['Refrigerator'],
             'Home > Refrigeración-Freezers', 1],
            ['cat4049', ['Refrigerator'],
             'Home > Refrigeración-Frigobar', 1],
            ['cat1840004', ['Refrigerator'],
             'Home > Refrigeración-Cavas', 1],
            ['cat3205', ['Refrigerator'],
             'Home > Refrigeración-Bottom freezer', 1,
             'f.product.attribute.Tipo=Bottom+freezer'],
            ['cat3205', ['Refrigerator'],
             'Home > Refrigeración-Top mount', 1,
             'f.product.attribute.Tipo=Top+mount'],
            ['cat1820006', ['Printer'],
             'Home > Computación-Impresión > Impresoras Multifuncionales', 1],
            # ['cat6680042/Impresoras-Tradicionales', 'Printer'],
            # ['cat11970007/Impresoras-Laser', 'Printer'],
            # ['cat11970009/Impresoras-Fotograficas', 'Printer'],
            ['cat3151', ['Oven'],
             'Home > Microondas', 1],
            ['cat3114', ['Oven'],
             'Home > Electrodomésticos Cocina- Electrodomésticos de cocina > '
             'Hornos Eléctricos', 1],
            # ['cat3025', ['VacuumCleaner'],
            #  'Home > Electrohogar- Aspirado y Limpieza > Aspiradoras', 1],
            ['cat3136', ['WashingMachine'],
             'Home > Electrohogar-Lavado > Lavado', 1],
            ['cat4060', ['WashingMachine'],
             'Home > Electrohogar-Lavado > Lavadoras', 1],
            ['cat1700002', ['WashingMachine'],
             'Home > Electrohogar-Lavado > Lavadoras-Secadoras', 1],
            ['cat4088', ['WashingMachine'],
             'Home > Electrohogar-Lavado > Secadoras', 1],
            ['cat1280018', ['Cell'],
             'Home > Telefonía- Celulares y Teléfonos > Celulares Básicos', 1],
            ['cat720161', ['Cell'],
             'Home > Telefonía- Celulares y Teléfonos > Smartphones', 1],
            ['cat70028', ['Camera'],
             'Home > Fotografía-Cámaras Compactas', 1],
            ['cat70029', ['Camera'],
             'Home > Fotografía-Cámaras Semiprofesionales', 1],
            ['cat3091', ['StereoSystem'],
             'Home > Audio-Equipos de Música y Karaokes', 1],
            ['cat3171', ['StereoSystem'],
             'Home > Computación- Accesorios Tecnología > Accesorios Audio > '
             'Parlantes Bluetooth', 1],
            ['cat2045', ['StereoSystem'],
             'Home > Audio-Soundbar y Home Theater', 1],
            ['cat1130010', ['StereoSystem'],
             'Home > Audio- Hi-Fi > Tornamesas', 1],
            ['cat6260041', ['StereoSystem'],
             'Home > Día del Niño Chile- Tecnología > Audio > Karaoke', 1],
            ['cat2032', ['OpticalDiskPlayer'],
             'Home > TV-Blu Ray y DVD', 1],
            ['cat3087', ['ExternalStorageDrive'],
             'Home > Computación- Almacenamiento > Discos duros', 1],
            ['cat3177', ['UsbFlashDrive'],
             'Home > Computación- Almacenamiento > Pendrives', 1],
            ['cat70037', ['MemoryCard'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Fotografía > Tarjetas de Memoria', 1],
            ['cat2070', ['Projector'],
             'Home > TV-Proyectores', 1],
            ['cat3770004', ['VideoGameConsole'],
             'Home > Tecnología- Videojuegos > Consolas', 1],
            ['cat40051', ['AllInOne'],
             'Home > Computación-All In One', 1],
            ['cat7830015', ['AirConditioner'],
             'Home > Electrohogar- Aire Acondicionado > Portátiles', 1],
            ['cat7830014', ['AirConditioner'],
             'Home > Electrohogar- Aire Acondicionado >Split', 1],
            ['cat3197', ['AirConditioner'],
             'Home > Electrohogar- Aire Acondicionado > Purificadores', 1],
            ['cat2062', ['Monitor'],
             'Home > Computación-Monitores', 1],
            ['cat2013', ['WaterHeater'],
             'Home > Electrohogar- Aire Acondicionado > Calefont y Termos', 1],
            ['cat3155', ['Mouse'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Computación > Mouse', 1],
            ['cat9900007', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Parafina Láser', 1],
            ['cat9910024', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Gas', 1],
            ['cat9910006', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Eléctricas', 1],
            ['cat9910027', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Pellet y Leña', 1],
            ['cat4290063', ['Wearable'],
             'Home > Telefonía- Wearables > SmartWatch', 1],
            ['cat4730023', ['Keyboard'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Computación > Teclados > Teclados Gamers', 1],
            ['cat2370002', ['Keyboard'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Computación > Teclados', 1],
            # ['cat2930003', ['Keyboard'],
            #  'Home > Computación- Accesorios Tecnología > Accesorios TV > '
            #  'Teclados Smart', 1],
            ['cat1640002', ['Headphones'],
             'Home > Computación- Accesorios Tecnología > Accesorios Audio > '
             'Audífonos', 1],
            ['cat4061', ['DishWasher'],
             'Home > Lavado-Lavavajillas', 1],
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = CF_REQUEST_HEADERS['User-Agent']
        products_dict = {}

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = \
                e[:4]

            if len(e) > 4:
                extra_query_params = e[4]
            else:
                extra_query_params = None

            if category not in local_categories:
                continue

            category_products = cls._get_products(
                session, category_id, category, extra_query_params)

            for idx, product in enumerate(category_products):
                if product.sku in products_dict:
                    product_to_update = products_dict[product.sku]
                else:
                    products_dict[product.sku] = product
                    product_to_update = product

                product_to_update.positions[section_name] = idx + 1

        products_list = [p for p in products_dict.values()]
        return products_list

    @classmethod
    def _get_products(cls, session, category_id, category, extra_query_params):
        products = []
        base_url = 'https://www.falabella.com/s/browse/v1/listing/cl?' \
                   'zone=13&categoryId={}&page={}'

        page = 1

        while True:
            if page > 60:
                raise Exception('Page overflow: ' + category_id)

            pag_url = base_url.format(category_id, page)
            print(pag_url)

            if extra_query_params:
                pag_url += '&' + extra_query_params

            res = session.get(pag_url, timeout=None)
            res = json.loads(res.content.decode('utf-8'))['data']

            if 'results' not in res:
                if page == 1:
                    raise Exception('Empty category: {}'.format(category_id))
                break

            for result in res['results']:
                product_url = result['url']
                product_name = result['displayName']
                product_sku = result['skuId']
                product_stock = -1

                prices = result['prices']
                offer_price = None
                normal_price = None

                for price in prices:
                    if price['label'] == '(Oferta)':
                        offer_price = Decimal(remove_words(price['price'][0]))
                    else:
                        normal_price = Decimal(remove_words(price['price'][0]))

                if not normal_price:
                    normal_price = offer_price

                if not offer_price:
                    offer_price = normal_price

                print(product_url)

                p = Product(
                    product_name,
                    cls.__name__,
                    category,
                    product_url,
                    product_url,
                    product_sku,
                    product_stock,
                    normal_price,
                    offer_price,
                    'CLP',
                    sku=product_sku,
                )
                products.append(p)

            page += 1

        return products
