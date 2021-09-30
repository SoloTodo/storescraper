import json
import logging

import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import UPS, NOTEBOOK, STORAGE_DRIVE, MONITOR, \
    HEADPHONES, MOUSE, KEYBOARD, CPU_COOLER, POWER_SUPPLY, COMPUTER_CASE, \
    RAM, GAMING_CHAIR, PRINTER, TABLET, KEYBOARD_MOUSE_COMBO, CELL, \
    CELL_ACCESORY, WEARABLE, VIDEO_GAME, CAMERA, MEMORY_CARD, \
    USB_FLASH_DRIVE, STEREO_SYSTEM, ALL_IN_ONE, VIDEO_GAME_CONSOLE, \
    SOLID_STATE_DRIVE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MercadoLibreChile(Store):
    @classmethod
    def categories(cls):
        return [i for i in set(cls.ml_categories().values()) if i]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        for store_extension, _foo in cls._category_paths().items():
            offset = 1
            while True:
                if offset > 1000:
                    raise Exception('Page overflow')

                url_webpage = 'https://listado.mercadolibre.cl/_Desde_{}{}'. \
                    format(offset, store_extension)
                print(url_webpage)
                response = session.get(url_webpage)
                json_container = re.search(
                    r'window.__PRELOADED_STATE__ =([\S\s]+?);\n',
                    response.text)
                if not json_container:
                    break
                product_json = json.loads(json_container.groups()[0])
                product_containers = product_json['initialState']['results']
                if not product_containers:
                    if offset == 1:
                        logging.warning('Empty category: ' + store_extension)
                    break
                categories_code = cls.ml_code_categories()
                ml_categories = cls.ml_categories()
                for product in product_containers:
                    product_category = ml_categories[
                        categories_code[product['category_id']]]
                    if product_category != category:
                        continue
                    product_url = product['permalink'].split('?')[0]
                    product_urls.append(product_url)

                offset += 48

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        new_mode_data = re.search(
            r'window.__PRELOADED_STATE__ =([\S\s]+?);\n', page_source)
        data = json.loads(new_mode_data.groups()[0])

        for entry in data['initialState']['components'].get('head', []):
            if entry['id'] == 'item_status_message' and 'PAUSADA' in \
                    entry['body']['text'].upper():
                return []
        if 'component_id' in data['initialState']['components'][
            'variations']:
            return cls.retrieve_type2_products(session, url, soup,
                                               category, data)
        else:
            return cls.retrieve_type3_products(data, session, category)

    @classmethod
    def retrieve_type3_products(cls, data, session, category):
        print('Type3')
        variations = set()
        pickers = data['initialState']['components']['variations'].get(
            'pickers', None)

        if pickers:
            for picker in pickers:
                for product in picker['products']:
                    variations.add(product['id'])
        else:
            variations.add(data['initialState']['id'])

        products = []

        for variation in variations:
            sku = variation
            endpoint = 'https://www.mercadolibre.cl/p/api/products/' + \
                       variation
            variation_data = json.loads(session.get(endpoint).text)
            if variation_data['schema'][0]['offers']['availability'] == \
                    'https://schema.org/OutOfStock':
                # No price information in this case, so skip it
                continue

            if variation_data['components']['seller']['state'] == 'HIDDEN':
                continue

            name = variation_data['components']['header']['title']
            seller = variation_data['components']['seller']['title_value']
            url = variation_data['components']['metadata']['url_canonical']
            price = Decimal(variation_data['components']['price']['price']
                            ['value'])
            picture_template = variation_data['components']['gallery'][
                'picture_config']['template']
            picture_urls = []
            for picture in variation_data['components']['gallery']['pictures']:
                picture_urls.append(picture_template.format(id=picture['id']))

            products.append(Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                -1,
                price,
                price,
                'CLP',
                sku=sku,
                seller=seller,
                picture_urls=picture_urls,
                description='Type3'
            ))

        return products

    @classmethod
    def retrieve_type2_products(cls, session, url, soup, category, data):
        print('Type2')
        seller = data['initialState']['components']['track'][
            'analytics_event']['custom_dimensions'][
            'customDimensions']['officialStore']
        sku = data['initialState']['id']
        base_name = data['initialState']['components'][
            'short_description'][0]['title']
        price = Decimal(data['initialState']['schema'][0][
                            'offers']['price'])

        picker = None
        for x in data['initialState']['components']['short_description']:
            if x['id'] == 'variations' and 'pickers' in x:
                if len(x['pickers']) == 1:
                    picker = x['pickers'][0]
                else:
                    # I'm not sure how to handle multiple pickers
                    # https://articulo.mercadolibre.cl/MLC-547289939-
                    # samartband-huawei-band-4-pro-_JM
                    picker = None

        products = []

        if picker:
            picker_id = picker['id']
            for variation in picker['products']:
                color_name = variation['label']['text']
                name = '{} ({})'.format(base_name, color_name)
                color_id = variation['attribute_id']

                variation_url = '{}?attributes={}:{}'.format(url, picker_id,
                                                             color_id)
                res = session.get(variation_url)
                key_match = re.search(r'variation=(\d+)', res.url)

                if key_match:
                    key = key_match.groups()[0]
                    variation_url = '{}?variation={}'.format(url, key)
                else:
                    key = variation['id']

                products.append(Product(
                    name,
                    cls.__name__,
                    category,
                    variation_url,
                    url,
                    key,
                    -1,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    seller=seller,
                    description='Type2'
                ))
        else:
            picture_urls = [x['data-zoom'] for x in
                            soup.findAll('img', 'ui-pdp-image')[1::2]
                            if 'data-zoom' in x.attrs]
            products.append(Product(
                base_name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                -1,
                price,
                price,
                'CLP',
                sku=sku,
                seller=seller,
                picture_urls=picture_urls,
                description='Type2'
            ))
        return products

    @classmethod
    def _category_paths(cls):
        return {
            '_Tienda_mercado-libre-gaming': VIDEO_GAME_CONSOLE,
            '_Tienda_microplay': VIDEO_GAME_CONSOLE,
            '_Tienda_playstation': VIDEO_GAME_CONSOLE,
            '_Tienda_ubisoft': VIDEO_GAME_CONSOLE,
            '_Tienda_warner-bros-games': VIDEO_GAME_CONSOLE,
            '_Tienda_acer': NOTEBOOK,
            '_Tienda_hp': NOTEBOOK,

        }

    @classmethod
    def ml_code_categories(cls):
        return \
            {
                "MLC1720": "UPS",
                "MLC1722": "Otros",
                "MLC1648": "Computación",
                "MLC3937": "Relojes y Joyas",
                "MLC430598": "Almacenamiento",
                "MLC1655": "Monitores y Accesorios",
                "MLC430687": "Notebooks y Accesorios",
                "MLC3377": "Accesorios para Notebooks",
                "MLC1652": "Notebooks",
                "MLC157821": "Ultrabooks",
                "MLC1000": "Electrónica, Audio y Video",
                "MLC430794": "Cables de Red y Accesorios",
                "MLC430901": "Routers",
                "MLC440652": "Switches",
                "MLC447778": "Accesorios para PC Gaming",
                "MLC1691": "Componentes de PC",
                "MLC454379": "Periféricos de PC",
                "MLC1714": "Mouses",
                "MLC1713": "Teclados",
                "MLC430788": "Coolers y Ventiladores",
                "MLC430796": "Discos y Accesorios",
                "MLC430916": "Fuentes de Alimentación",
                "MLC1696": "Gabinetes y Soportes de PC",
                "MLC1694": "Memorias RAM",
                "MLC6777": "Audífonos",
                "MLC447782": "Sillas Gamer",
                "MLC1700": "Conectividad y Redes",
                "MLC440656": "Adaptadores USB",
                "MLC1706": "Tarjetas de Red",
                "MLC1574": "Hogar y Muebles",
                "MLC1430": "Vestuario y Calzado",
                "MLC177923": "Impresión",
                "MLC430637": "PC de Escritorio",
                "MLC433676": "Tablets y Accesorios",
                "MLC6263": "Kits de Mouse y Teclado",
                "MLC1716": "Mouse Pads",
                "MLC6593": "Cables y Adaptadores",
                "MLC40749": "Fundas",
                "MLC7223": "Mochilas, Maletines y Fundas",
                "MLC1676": "Impresoras",
                "MLC2141": "Insumos de Impresión",
                "MLC7415": "Cartuchos de Tinta",
                "MLC10871": "Tintas",
                "MLC3560": "Toners",
                "MLC1051": "Celulares y Telefonía",
                "MLC157822": "Netbooks",
                "MLC3813": "Accesorios para Celulares",
                "MLC1055": "Celulares y Smartphones",
                "MLC417704": "Smartwatches y Accesorios",
                "MLC436011": "Adaptadores",
                "MLC4922": "Cables de Datos",
                "MLC432437": "Carcasas, Fundas y Protectores",
                "MLC5546": "Cargadores",
                "MLC5549": "Otros",
                "MLC85756": "Accesorios",
                "MLC159250": "Repuestos",
                "MLC82067": "Tablets",
                "MLC1144": "Consolas y Videojuegos",
                "MLC3697": "Audífonos",
                "MLC440366": "Micrófonos y Preamplificadores",
                "MLC438578": "Accesorios para Consolas",
                "MLC439527": "Accesorios para PC Gaming",
                "MLC439596": "Audífonos",
                "MLC191054": "Micrófonos",
                "MLC159228": "Para PlayStation",
                "MLC159227": "Para Xbox",
                "MLC180910": "Fuentes de Alimentación",
                "MLC180896": "Headsets",
                "MLC440885": "Micrófonos",
                "MLC436380": "Muebles para el Hogar",
                "MLC436246": "Textiles de Hogar y Decoración",
                "MLC11878": "Candados de Seguridad",
                "MLC40780": "Controles Remotos",
                "MLC3581": "Docking Stations",
                "MLC440858": "Hubs USB",
                "MLC3584": "Otros",
                "MLC26532": "Maletines y Bolsos",
                "MLC26538": "Mochilas",
                "MLC418042": "Bases",
                "MLC431333": "Filtros para Monitor",
                "MLC418043": "Soportes",
                "MLC1039": "Cámaras y Accesorios",
                "MLC3553": "Memorias Digitales",
                "MLC430373": "Otros",
                "MLC1669": "Discos y Accesorios",
                "MLC1673": "Pen Drives",
                "MLC1022": "Parlantes y Subwoofers",
                "MLC430918": "Cables y Hubs USB",
                "MLC159231": "Estuches y Fundas",
                "MLC159241": "Lápices Touch",
                "MLC1667": "Cámaras Web",
                "MLC430630": "Mouses y Teclados",
                "MLC181025": "All In One",
                "MLC1649": "Computadores",
                "MLC178644": "Mini PCs",
                "MLC9240": "Cargadores y Fuentes",
                "MLC175552": "Soportes",
                "MLC1012": "Audio Portátil y Accesorios",
                "MLC3378": "Parlantes para PC",
                "MLC440657": "Controles para Gamers",
                "MLC447784": "Otros",
                "MLC448169": "Controles para Gamers",
                "MLC1384": "Bebés",
                "MLC1276": "Deportes y Fitness",
                "MLC431994": "Equipaje y Accesorios de Viaje",
                "MLC31406": "Mochilas",
                "MLC159245": "Láminas Protectoras",
                "MLC440682": "Repuestos para Notebooks",
                "MLC54182": "Bases Enfriadoras",
                "MLC17800": "Antenas Wireless",
                "MLC3690": "Accesorios para Audio y Video",
                "MLC1010": "Audio",
                "MLC1070": "Otros",
                "MLC1014": "Micro y Minicomponentes",
                "MLC438566": "Consolas",
                "MLC187264": "Sillas Gamer",
                "MLC159229": "Para Nintendo",
                "MLC455247": "Fundas y Estuches",
                "MLC455248": "Otros",
                "MLC116370": "PS4 - PlayStation 4",
                "MLC455263": "PS5 - PlayStation 5",
                "MLC439072": "Audio y Video para Gaming",
                "MLC180981": "Cargadores",
                "MLC413744": "Fundas para Controles",
                "MLC432435": "Colgantes y Soportes",
                "MLC5542": "Manos Libres",
                "MLC157688": "Inalambrico",
                "MLC157686": "Portatiles",
                "MLC430797": "Accesorios",
                "MLC1672": "Discos Duros y SSDs",
                "MLC10190": "Repuestos",
                "MLC1499": "Industrias y Oficinas",
                "MLC9183": "Sillas",
                "MLC412717": "Sillas Tándem",
                "MLC431414": "Accesorios para TV",
                "MLC5054": "Cables",
                "MLC58760": "Cables de Audio y Video",
                "MLC36587": "Otros Cables",
                "MLC10177": "Home Theater",
                "MLC108729": "Soportes para Parlantes",
                "MLC1715": "Cables",
                "MLC9729": "Hubs USB",
                "MLC5068": "Baterías"
            }

    @classmethod
    def ml_categories(cls):
        return \
            {
                "UPS": UPS,
                "Otros": None,
                "Computación": NOTEBOOK,
                "Relojes y Joyas": None,
                "Almacenamiento": STORAGE_DRIVE,
                "Monitores y Accesorios": MONITOR,
                "Notebooks y Accesorios": NOTEBOOK,
                "Accesorios para Notebooks": None,
                "Notebooks": NOTEBOOK,
                "Ultrabooks": NOTEBOOK,
                "Electrónica, Audio y Video": HEADPHONES,
                "Cables de Red y Accesorios": None,
                "Routers": None,
                "Switches": None,
                "Accesorios para PC Gaming": MOUSE,
                "Componentes de PC": NOTEBOOK,
                "Periféricos de PC": KEYBOARD,
                "Mouses": MOUSE,
                "Teclados": KEYBOARD,
                "Coolers y Ventiladores": CPU_COOLER,
                "Discos y Accesorios": None,
                "Fuentes de Alimentación": POWER_SUPPLY,
                "Gabinetes y Soportes de PC": COMPUTER_CASE,
                "Memorias RAM": RAM,
                "Audífonos": HEADPHONES,
                "Sillas Gamer": GAMING_CHAIR,
                "Conectividad y Redes": None,
                "Adaptadores USB": None,
                "Tarjetas de Red": None,
                "Hogar y Muebles": None,
                "Vestuario y Calzado": None,
                "Impresión": PRINTER,
                "PC de Escritorio": None,
                "Tablets y Accesorios": TABLET,
                "Kits de Mouse y Teclado": KEYBOARD_MOUSE_COMBO,
                "Mouse Pads": None,
                "Cables y Adaptadores": None,
                "Fundas": None,
                "Mochilas, Maletines y Fundas": None,
                "Impresoras": PRINTER,
                "Insumos de Impresión": None,
                "Cartuchos de Tinta": None,
                "Tintas": None,
                "Toners": None,
                "Celulares y Telefonía": CELL,
                "Netbooks": NOTEBOOK,
                "Accesorios para Celulares": CELL_ACCESORY,
                "Celulares y Smartphones": CELL,
                "Smartwatches y Accesorios": WEARABLE,
                "Adaptadores": None,
                "Cables de Datos": None,
                "Carcasas, Fundas y Protectores": CELL_ACCESORY,
                "Cargadores": None,
                "Accesorios": None,
                "Repuestos": None,
                "Tablets": TABLET,
                "Consolas y Videojuegos": VIDEO_GAME,
                "Micrófonos y Preamplificadores": None,
                "Accesorios para Consolas": None,
                "Micrófonos": None,
                "Para PlayStation": None,
                "Para Xbox": None,
                "Headsets": HEADPHONES,
                "Muebles para el Hogar": None,
                "Textiles de Hogar y Decoración": None,
                "Candados de Seguridad": None,
                "Controles Remotos": None,
                "Docking Stations": None,
                "Hubs USB": None,
                "Maletines y Bolsos": None,
                "Mochilas": None,
                "Bases": None,
                "Filtros para Monitor": None,
                "Soportes": None,
                "Cámaras y Accesorios": CAMERA,
                "Memorias Digitales": MEMORY_CARD,
                "Pen Drives": USB_FLASH_DRIVE,
                "Parlantes y Subwoofers": STEREO_SYSTEM,
                "Cables y Hubs USB": None,
                "Estuches y Fundas": None,
                "Lápices Touch": None,
                "Cámaras Web": None,
                "Mouses y Teclados": KEYBOARD_MOUSE_COMBO,
                "All In One": ALL_IN_ONE,
                "Computadores": NOTEBOOK,
                "Mini PCs": NOTEBOOK,
                "Cargadores y Fuentes": POWER_SUPPLY,
                "Audio Portátil y Accesorios": STEREO_SYSTEM,
                "Parlantes para PC": STEREO_SYSTEM,
                "Controles para Gamers": None,
                "Bebés": None,
                "Deportes y Fitness": None,
                "Equipaje y Accesorios de Viaje": None,
                "Láminas Protectoras": None,
                "Repuestos para Notebooks": None,
                "Bases Enfriadoras": None,
                "Antenas Wireless": None,
                "Accesorios para Audio y Video": None,
                "Audio": STEREO_SYSTEM,
                "Micro y Minicomponentes": STEREO_SYSTEM,
                "Consolas": VIDEO_GAME_CONSOLE,
                "Para Nintendo": VIDEO_GAME_CONSOLE,
                "Fundas y Estuches": None,
                "PS4 - PlayStation 4": VIDEO_GAME_CONSOLE,
                "PS5 - PlayStation 5": VIDEO_GAME_CONSOLE,
                "Audio y Video para Gaming": HEADPHONES,
                "Fundas para Controles": None,
                "Colgantes y Soportes": None,
                "Manos Libres": None,
                "Inalambrico": None,
                "Portatiles": NOTEBOOK,
                "Discos Duros y SSDs": SOLID_STATE_DRIVE,
                "Industrias y Oficinas": None,
                "Sillas": GAMING_CHAIR,
                "Sillas Tándem": GAMING_CHAIR,
                "Accesorios para TV": None,
                "Cables de Audio y Video": None,
                "Otros Cables": None,
                "Home Theater": STEREO_SYSTEM,
                "Soportes para Parlantes": None,
                "Baterías": None
            }
