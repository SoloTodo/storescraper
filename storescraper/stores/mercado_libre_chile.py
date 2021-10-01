import json
import logging

import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, NOTEBOOK, STEREO_SYSTEM, KEYBOARD, \
    MOUSE, CELL_ACCESORY, WEARABLE, TABLET, REFRIGERATOR, HEADPHONES, \
    CAMERA, KEYBOARD_MOUSE_COMBO, VIDEO_GAME_CONSOLE, MONITOR, PROJECTOR, \
    MEMORY_CARD, GAMING_CHAIR, STORAGE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, \
    USB_FLASH_DRIVE, RAM, TELEVISION, AIR_CONDITIONER, OVEN, WASHING_MACHINE, \
    LAMP, UPS, ALL_IN_ONE, VIDEO_CAMERA, STOVE, PROCESSOR, VACUUM_CLEANER, \
    DISH_WASHER, PRINTER, VIDEO_GAME
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
        category = NOTEBOOK
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
        return {
            "MLC1051": "Celulares y Telefonía",
            "MLC1648": "Computación",
            "MLC1000": "Electrónica, Audio y Video",
            "MLC1574": "Hogar y Muebles",
            "MLC1010": "Audio",
            "MLC5054": "Cables",
            "MLC4632": "Controles Remotos",
            "MLC430918": "Cables y Hubs USB",
            "MLC430687": "Notebooks y Accesorios",
            "MLC454379": "Periféricos de PC",
            "MLC433676": "Tablets y Accesorios",
            "MLC159241": "Lápices Touch",
            "MLC159232": "Teclados",
            "MLC1714": "Mouses",
            "MLC1713": "Teclados",
            "MLC373735": "Trackpads",
            "MLC6593": "Cables y Adaptadores",
            "MLC11878": "Candados de Seguridad",
            "MLC3813": "Accesorios para Celulares",
            "MLC417704": "Smartwatches y Accesorios",
            "MLC417755": "Cargadores",
            "MLC434353": "Mallas",
            "MLC436011": "Adaptadores",
            "MLC4922": "Cables de Datos",
            "MLC432437": "Carcasas, Fundas y Protectores",
            "MLC5546": "Cargadores",
            "MLC5549": "Otros",
            "MLC157684": "Cargadores con Cable",
            "MLC157688": "Inalambrico",
            "MLC49334": "Para TV",
            "MLC49342": "Otros",
            "MLC116538": "Smartwatches",
            "MLC85756": "Accesorios",
            "MLC82067": "Tablets",
            "MLC430637": "PC de Escritorio",
            "MLC3690": "Accesorios para Audio y Video",
            "MLC157822": "Netbooks",
            "MLC1652": "Notebooks",
            "MLC1055": "Celulares y Smartphones",
            "MLC5726": "Electrodomésticos",
            "MLC1430": "Vestuario y Calzado",
            "MLC1012": "Audio Portátil y Accesorios",
            "MLC3697": "Audífonos",
            "MLC440071": "Artefactos de Cuidado Personal",
            "MLC1581": "Pequeños Electrodomésticos",
            "MLC1667": "Cámaras Web",
            "MLC430630": "Mouses y Teclados",
            "MLC1053": "Telefonía Fija e Inalámbrica",
            "MLC432435": "Colgantes y Soportes",
            "MLC439917": "Apoya Celulares",
            "MLC439919": "Porta Celulares",
            "MLC157686": "Portatiles",
            "MLC157694": "Carcasas y Fundas",
            "MLC175454": "Cases",
            "MLC12953": "Láminas Protectoras",
            "MLC1144": "Consolas y Videojuegos",
            "MLC1500": "Construcción",
            "MLC1132": "Juegos y Juguetes",
            "MLC1582": "Iluminación para el Hogar",
            "MLC177170": "Seguridad para el Hogar",
            "MLC1066": "Alarmas y Sensores",
            "MLC179831": "Circuito de Cámaras",
            "MLC5713": "Cámaras de Vigilancia",
            "MLC438578": "Accesorios para Consolas",
            "MLC439527": "Accesorios para PC Gaming",
            "MLC455245": "Xbox Series X/S",
            "MLC161962": "Otros Xboxs",
            "MLC447778": "Accesorios para PC Gaming",
            "MLC1655": "Monitores y Accesorios",
            "MLC6263": "Kits de Mouse y Teclado",
            "MLC1747": "Accesorios para Vehículos",
            "MLC1071": "Animales y Mascotas",
            "MLC1368": "Arte, Librería y Cordonería",
            "MLC1384": "Bebés",
            "MLC1246": "Belleza y Cuidado Personal",
            "MLC1039": "Cámaras y Accesorios",
            "MLC1276": "Deportes y Fitness",
            "MLC3025": "Libros, Revistas y Comics",
            "MLC3937": "Relojes y Joyas",
            "MLC409431": "Salud y Equipamiento Médico",
            "MLC174421": "Pesas de Baño",
            "MLC66176": "Termómetros",
            "MLC435370": "Otros",
            "MLC3948": "Relojes Murales",
            "MLC399230": "Smartwatches",
            "MLC1631": "Adornos y Decoración del Hogar",
            "MLC1592": "Cocina y Menaje",
            "MLC436380": "Muebles para el Hogar",
            "MLC436246": "Textiles de Hogar y Decoración",
            "MLC177171": "Porteros Eléctricos",
            "MLC163740": "Ampolletas",
            "MLC163822": "Cintas LED",
            "MLC431414": "Accesorios para TV",
            "MLC11830": "Componentes Electrónicos",
            "MLC174349": "Media Streaming",
            "MLC9239": "Proyectores y Telones",
            "MLC409415": "Asistentes Virtuales",
            "MLC1024": "Equipos de DJ y Accesorios",
            "MLC440366": "Micrófonos y Preamplificadores",
            "MLC1362": "Camping, Caza y Pesca",
            "MLC410723": "Monopatines y Scooters",
            "MLC1049": "Accesorios para Cámaras",
            "MLC4660": "Filmadoras y Cámaras de Acción",
            "MLC420011": "Estudio e Iluminación",
            "MLC174272": "Para Cámaras de Acción",
            "MLC430367": "Tarjetas de Memoria y Lectores",
            "MLC439596": "Audífonos",
            "MLC448169": "Controles para Gamers",
            "MLC187264": "Sillas Gamer",
            "MLC439597": "Otros",
            "MLC159228": "Para PlayStation",
            "MLC159227": "Para Xbox",
            "MLC116370": "PS4 - PlayStation 4",
            "MLC455263": "PS5 - PlayStation 5",
            "MLC440985": "Cables y Adaptadores",
            "MLC116375": "Otros",
            "MLC430598": "Almacenamiento",
            "MLC1691": "Componentes de PC",
            "MLC1700": "Conectividad y Redes",
            "MLC1657": "Proyectores y Telones",
            "MLC1723": "Software",
            "MLC159231": "Estuches y Fundas",
            "MLC159245": "Láminas Protectoras",
            "MLC3378": "Parlantes para PC",
            "MLC1716": "Mouse Pads",
            "MLC440873": "Tabletas Digitalizadoras",
            "MLC3377": "Accesorios para Notebooks",
            "MLC54182": "Bases Enfriadoras",
            "MLC9240": "Cargadores y Fuentes",
            "MLC40749": "Fundas",
            "MLC440858": "Hubs USB",
            "MLC7223": "Mochilas, Maletines y Fundas",
            "MLC3584": "Otros",
            "MLC418042": "Bases",
            "MLC21069": "Monitores",
            "MLC440656": "Adaptadores USB",
            "MLC430794": "Cables de Red y Accesorios",
            "MLC430901": "Routers",
            "MLC430788": "Coolers y Ventiladores",
            "MLC430796": "Discos y Accesorios",
            "MLC430916": "Fuentes de Alimentación",
            "MLC1696": "Gabinetes y Soportes de PC",
            "MLC1715": "Cables",
            "MLC9729": "Hubs USB",
            "MLC5895": "Cables de Audio y Video",
            "MLC5877": "Cables de Datos",
            "MLC1669": "Discos y Accesorios",
            "MLC1673": "Pen Drives",
            "MLC6777": "Audífonos",
            "MLC440657": "Controles para Gamers",
            "MLC447782": "Sillas Gamer",
            "MLC447784": "Otros",
            "MLC417705": "Otros",
            "MLC5107": "Cables de Audio y Video",
            "MLC175456": "Joysticks",
            "MLC7908": "Memorias",
            "MLC58500": "Soportes para Vehiculos",
            "MLC432439": "Otros",
            "MLC420040": "Fundas Cargadoras",
            "MLC157689": "Otros",
            "MLC5702": "Artículos de Bebé para Baños",
            "MLC1392": "Juegos y Juguetes para Bebés",
            "MLC22867": "Accesorios de Auto y Camioneta",
            "MLC3381": "Audio para Vehículos",
            "MLC1058": "Handies y Radiofrecuencia",
            "MLC5542": "Manos Libres",
            "MLC1002": "Televisores",
            "MLC10177": "Home Theater",
            "MLC1022": "Parlantes y Subwoofers",
            "MLC2531": "Climatización",
            "MLC1580": "Hornos y Cocinas",
            "MLC1578": "Lavado",
            "MLC1576": "Refrigeración",
            "MLC9456": "Refrigeradores",
            "MLC179816": "Repuestos y Accesorios",
            "MLC4337": "Aspiradoras",
            "MLC180993": "Aspiradoras Robot",
            "MLC455108": "Repuestos y Accesorios",
            "MLC178593": "Lavadora-Secadoras",
            "MLC174300": "Lavavajillas",
            "MLC27590": "Secadoras",
            "MLC29800": "Aires Acondicionados",
            "MLC176937": "Repuestos y Accesorios",
            "MLC39109": "Lápices y Uñetas",
            "MLC178483": "Herramientas",
            "MLC1499": "Industrias y Oficinas",
            "MLC1953": "Otras Categorías",
            "MLC431994": "Equipaje y Accesorios de Viaje",
            "MLC31406": "Mochilas",
            "MLC435064": "Tratamientos Respiratorios",
            "MLC179796": "Humidificadores",
            "MLC179017": "Purificadores de Aire",
            "MLC163741": "Lámparas",
            "MLC1070": "Otros",
            "MLC438287": "Para Cocina",
            "MLC438286": "Para Hogar",
            "MLC439831": "Otros",
            "MLC440073": "Artefactos para el Cabello",
            "MLC440072": "Balanzas de Baño",
            "MLC1292": "Ciclismo",
            "MLC440627": "Pulsómetros y Cronómetros",
            "MLC179479": "Monociclos Eléctricos",
            "MLC455434": "Monopatines",
            "MLC178749": "De Pie",
            "MLC455437": "Eléctricos",
            "MLC163738": "Cámaras",
            "MLC436831": "Revelado y Laboratorio",
            "MLC17800": "Antenas Wireless",
            "MLC11860": "Parlantes",
            "MLC455192": "Artefactos para el Cabello",
            "MLC417575": "Barbería",
            "MLC1253": "Cuidado de la Piel",
            "MLC393366": "Higiene Personal",
            "MLC174815": "Cepillos",
            "MLC447211": "Cepillos Eléctricos",
            "MLC1720": "UPS",
            "MLC1722": "Otros",
            "MLC157821": "Ultrabooks",
            "MLC440652": "Switches",
            "MLC1694": "Memorias RAM",
            "MLC1706": "Tarjetas de Red",
            "MLC177923": "Impresión",
            "MLC1676": "Impresoras",
            "MLC2141": "Insumos de Impresión",
            "MLC7415": "Cartuchos de Tinta",
            "MLC10871": "Tintas",
            "MLC3560": "Toners",
            "MLC159250": "Repuestos",
            "MLC191054": "Micrófonos",
            "MLC159229": "Para Nintendo",
            "MLC180910": "Fuentes de Alimentación",
            "MLC180896": "Headsets",
            "MLC440885": "Micrófonos",
            "MLC40780": "Controles Remotos",
            "MLC3581": "Docking Stations",
            "MLC26532": "Maletines y Bolsos",
            "MLC26538": "Mochilas",
            "MLC431333": "Filtros de Privacidad",
            "MLC418043": "Soportes",
            "MLC3553": "Memorias Digitales",
            "MLC430373": "Otros",
            "MLC181025": "All In One",
            "MLC1649": "Computadores",
            "MLC178644": "Mini PCs",
            "MLC175552": "Soportes",
            "MLC440682": "Repuestos para Notebooks",
            "MLC1014": "Micro y Minicomponentes",
            "MLC438566": "Consolas",
            "MLC455247": "Fundas y Estuches",
            "MLC455248": "Otros",
            "MLC439072": "Audio y Video para Gaming",
            "MLC180981": "Cargadores",
            "MLC413744": "Fundas para Controles",
            "MLC430797": "Accesorios",
            "MLC1672": "Discos Duros y SSDs",
            "MLC10190": "Repuestos",
            "MLC9183": "Sillas",
            "MLC412717": "Sillas Tándem",
            "MLC58760": "Cables de Audio y Video",
            "MLC36587": "Otros Cables",
            "MLC108729": "Soportes para Parlantes",
            "MLC5068": "Baterías",
            "MLC159270": "Videojuegos",
            "MLC1367": "Antigüedades y Colecciones",
            "MLC1456": "Lentes y Accesorios",
            "MLC174662": "Llaveros",
            "MLC412056": "Paraguas",
            "MLC66190": "Lentes de Sol",
            "MLC66191": "Ópticos",
            "MLC66170": "Otros",
            "MLC433069": "Juegos de Agua y Playa",
            "MLC455425": "Juegos de Construcción",
            "MLC432988": "Juegos de Mesa y Cartas",
            "MLC436967": "Juegos de Salón",
            "MLC12037": "Juguetes Antiestrés e Ingenio",
            "MLC432818": "Juguetes de Oficios",
            "MLC432888": "Muñecos y Muñecas",
            "MLC1166": "Peluches",
            "MLC3422": "Figuras de Acción",
            "MLC2968": "Muñecas y Bebés",
            "MLC455651": "Puzzles",
            "MLC455518": "Trompos",
            "MLC437053": "Cartas Coleccionables R.P.G.",
            "MLC1161": "Juegos de Mesa",
            "MLC175991": "Puzzles",
            "MLC432989": "Otros",
            "MLC5541": "Pilas y Cargadores",
            "MLC440349": "Video",
            "MLC40673": "Cargadores de Pilas",
            "MLC9828": "Pilas",
            "MLC431488": "Amplificadores y Receivers",
            "MLC172273": "Pinballs y Arcade",
            "MLC2930": "PS2 - PlayStation 2",
            "MLC11623": "PS3 - PlayStation 3",
            "MLC455274": "Cargadores para Controles",
            "MLC455268": "Fundas para Controles",
            "MLC455266": "Gamepads y Joysticks",
            "MLC180980": "Controles",
            "MLC420068": "Fuentes de Alimentación",
            "MLC180986": "Skins",
            "MLC439615": "Controles y Joysticks",
            "MLC11625": "Otros",
            "MLC4396": "Game Boy Advance - GBA",
            "MLC2921": "Game Cube",
            "MLC178658": "Nintendo Switch",
            "MLC11223": "Nintendo Wii",
            "MLC116432": "Nintendo Wii U",
            "MLC161960": "Otros Nintendos",
            "MLC190762": "Fuentes de Alimentación",
            "MLC413678": "Fundas y Estuches",
            "MLC416556": "Gamepads y Joysticks",
            "MLC413679": "Protectores de Pantalla",
            "MLC178843": "Otros",
            "MLC431792": "Cables de Red",
            "MLC180937": "Cuadernos",
            "MLC440143": "Estuches de Lápices",
            "MLC177774": "Enfriadores de Aire",
            "MLC183159": "Estufas y Calefactores",
            "MLC161360": "Ventiladores",
            "MLC162501": "Planchas",
            "MLC162504": "Hervidores",
            "MLC439832": "Preparación de Alimentos",
            "MLC438297": "Preparación de Bebidas",
            "MLC162503": "Arroceras",
            "MLC440064": "Batidoras",
            "MLC411071": "Sartenes y Ollas Eléctricas",
            "MLC162507": "Tostadoras",
            "MLC30852": "Cocinas",
            "MLC174295": "Extractores y Purificadores",
            "MLC30854": "Hornos",
            "MLC436300": "Artículos de Vino y Coctelería",
            "MLC436280": "Cocción y Horneado",
            "MLC159273": "Utensilios de Preparación",
            "MLC436289": "Vajilla y Artículos de Servir",
            "MLC159287": "Bandejas",
            "MLC1604": "Cuchillería",
            "MLC159295": "Cuchillos de Cocina",
            "MLC159294": "Juegos de Cuchillería",
            "MLC455317": "Coladores y Tendederos",
            "MLC455321": "Medidores de Cocina",
            "MLC180827": "Otros",
            "MLC159285": "Baterías de Cocina",
            "MLC159283": "Ollas",
            "MLC159284": "Sartenes",
            "MLC440063": "Balanzas de Cocina",
            "MLC438291": "Máquinas para Postres",
            "MLC180819": "Licuadoras",
            "MLC438298": "Otros",
            "MLC4340": "Cafeteras",
            "MLC30109": "Otros",
            "MLC171531": "Encimeras",
            "MLC385176": "Calefonts y Termos",
            "MLC440149": "Sistemas de Monitoreo",
            "MLC174413": "Timbres",
            "MLC177173": "Otros",
            "MLC439844": "Dispensadores y Purificadores",
            "MLC455131": "Cepillos",
            "MLC455118": "Filtros",
            "MLC455113": "Otros",
            "MLC1621": "Jardín y Aire Libre",
            "MLC162500": "Freidoras",
            "MLC174302": "Hornos de Pan",
            "MLC30848": "Microondas",
            "MLC158419": "Cavas de Vino",
            "MLC158426": "Freezers",
            "MLC436298": "Almacenamiento y Organización",
            "MLC1593": "Vajilla",
            "MLC440224": "Fuentes",
            "MLC179055": "Jarras",
            "MLC30082": "Juegos de Vajilla",
            "MLC436277": "Afiladores",
            "MLC180832": "Moldes",
            "MLC159275": "Tablas para Picar",
            "MLC440222": "Bandejas, Asaderas y Fuentes",
            "MLC440124": "Baterías, Ollas y Sartenes",
            "MLC436281": "Otros",
            "MLC440219": "Vaporieras",
            "MLC1899": "Otros",
            "MLC455059": "Repuestos y Accesorios",
            "MLC30849": "Otros",
            "MLC392350": "Para Cocinas y Hornos",
            "MLC455060": "Otros",
            "MLC392406": "Calderas",
            "MLC29793": "Chimeneas y Salamandras",
            "MLC431237": "Calefonts",
            "MLC431238": "Termos",
            "MLC1613": "Baños",
            "MLC2521": "Piscinas y Accesorios",
            "MLC455386": "Spa Exterior",
            "MLC433511": "Calentadores",
            "MLC440092": "Limpieza y Mantenimiento",
            "MLC177072": "Piscinas",
            "MLC30988": "Otros",
            "MLC1590": "Otros",
            "MLC1616": "Accesorios para Baño",
            "MLC443824": "Tinas",
            "MLC439847": "Electricidad",
            "MLC180881": "Mobiliario para Baños",
            "MLC440069": "Jugueras",
            "MLC429556": "Minipimers",
            "MLC174293": "Parrillas Eléctricas",
            "MLC401945": "Otros",
            "MLC162502": "Sandwicheras",
            "MLC440067": "Procesadores",
            "MLC179543": "Waffleras",
            "MLC162505": "Yogurteras",
            "MLC436275": "Utensilios de Repostería",
            "MLC159296": "Tenedores",
            "MLC455100": "Para Aires Acondicionados",
            "MLC176940": "Para Calefont y Termos",
            "MLC435273": "Gasfitería",
            "MLC411938": "Mobiliario para Cocinas",
            "MLC438290": "Otros",
            "MLC440070": "Exprimidores Eléctricos",
            "MLC175499": "Mopas a Vapor"
        }

    @classmethod
    def ml_categories(cls):
        return {
            "Celulares y Telefonía": CELL,
            "Computación": NOTEBOOK,
            "Electrónica, Audio y Video": STEREO_SYSTEM,
            "Hogar y Muebles": None,
            "Audio": STEREO_SYSTEM,
            "Cables": None,
            "Controles Remotos": None,
            "Cables y Hubs USB": None,
            "Notebooks y Accesorios": NOTEBOOK,
            "Periféricos de PC": KEYBOARD,
            "Tablets y Accesorios": TABLET,
            "Lápices Touch": None,
            "Teclados": KEYBOARD,
            "Mouses": MOUSE,
            "Trackpads": None,
            "Cables y Adaptadores": None,
            "Candados de Seguridad": None,
            "Accesorios para Celulares": CELL_ACCESORY,
            "Smartwatches y Accesorios": WEARABLE,
            "Cargadores": None,
            "Mallas": None,
            "Adaptadores": None,
            "Cables de Datos": None,
            "Carcasas, Fundas y Protectores": None,
            "Otros": None,
            "Cargadores con Cable": None,
            "Inalambrico": None,
            "Para TV": None,
            "Smartwatches": WEARABLE,
            "Accesorios": None,
            "Tablets": TABLET,
            "PC de Escritorio": None,
            "Accesorios para Audio y Video": None,
            "Netbooks": NOTEBOOK,
            "Notebooks": NOTEBOOK,
            "Celulares y Smartphones": CELL,
            "Electrodomésticos": REFRIGERATOR,
            "Vestuario y Calzado": None,
            "Audio Portátil y Accesorios": STEREO_SYSTEM,
            "Audífonos": HEADPHONES,
            "Artefactos de Cuidado Personal": None,
            "Pequeños Electrodomésticos": OVEN,
            "Cámaras Web": CAMERA,
            "Mouses y Teclados": KEYBOARD_MOUSE_COMBO,
            "Telefonía Fija e Inalámbrica": None,
            "Colgantes y Soportes": None,
            "Apoya Celulares": CELL_ACCESORY,
            "Porta Celulares": CELL_ACCESORY,
            "Portatiles": NOTEBOOK,
            "Carcasas y Fundas": CELL_ACCESORY,
            "Cases": CELL_ACCESORY,
            "Láminas Protectoras": CELL_ACCESORY,
            "Consolas y Videojuegos": VIDEO_GAME_CONSOLE,
            "Construcción": None,
            "Juegos y Juguetes": None,
            "Iluminación para el Hogar": None,
            "Seguridad para el Hogar": None,
            "Alarmas y Sensores": None,
            "Circuito de Cámaras": None,
            "Cámaras de Vigilancia": None,
            "Accesorios para Consolas": None,
            "Accesorios para PC Gaming": None,
            "Xbox Series X/S": VIDEO_GAME_CONSOLE,
            "Otros Xboxs": None,
            "Monitores y Accesorios": MONITOR,
            "Kits de Mouse y Teclado": KEYBOARD_MOUSE_COMBO,
            "Accesorios para Vehículos": None,
            "Animales y Mascotas": None,
            "Arte, Librería y Cordonería": None,
            "Bebés": None,
            "Belleza y Cuidado Personal": None,
            "Cámaras y Accesorios": CAMERA,
            "Deportes y Fitness": None,
            "Libros, Revistas y Comics": None,
            "Relojes y Joyas": None,
            "Salud y Equipamiento Médico": None,
            "Pesas de Baño": None,
            "Termómetros": None,
            "Relojes Murales": None,
            "Adornos y Decoración del Hogar": None,
            "Cocina y Menaje": None,
            "Muebles para el Hogar": None,
            "Textiles de Hogar y Decoración": None,
            "Porteros Eléctricos": None,
            "Ampolletas": None,
            "Cintas LED": None,
            "Accesorios para TV": None,
            "Componentes Electrónicos": None,
            "Media Streaming": None,
            "Proyectores y Telones": PROJECTOR,
            "Asistentes Virtuales": None,
            "Equipos de DJ y Accesorios": None,
            "Micrófonos y Preamplificadores": None,
            "Camping, Caza y Pesca": None,
            "Monopatines y Scooters": None,
            "Accesorios para Cámaras": None,
            "Filmadoras y Cámaras de Acción": None,
            "Estudio e Iluminación": None,
            "Para Cámaras de Acción": None,
            "Tarjetas de Memoria y Lectores": MEMORY_CARD,
            "Controles para Gamers": None,
            "Sillas Gamer": GAMING_CHAIR,
            "Para PlayStation": None,
            "Para Xbox": None,
            "PS4 - PlayStation 4": VIDEO_GAME_CONSOLE,
            "PS5 - PlayStation 5": VIDEO_GAME_CONSOLE,
            "Almacenamiento": STORAGE_DRIVE,
            "Componentes de PC": None,
            "Conectividad y Redes": None,
            "Software": None,
            "Estuches y Fundas": None,
            "Parlantes para PC": STEREO_SYSTEM,
            "Mouse Pads": None,
            "Tabletas Digitalizadoras": TABLET,
            "Accesorios para Notebooks": None,
            "Bases Enfriadoras": None,
            "Cargadores y Fuentes": None,
            "Fundas": None,
            "Hubs USB": None,
            "Mochilas, Maletines y Fundas": None,
            "Bases": None,
            "Monitores": MONITOR,
            "Adaptadores USB": None,
            "Cables de Red y Accesorios": None,
            "Routers": None,
            "Coolers y Ventiladores": None,
            "Discos y Accesorios": None,
            "Fuentes de Alimentación": POWER_SUPPLY,
            "Gabinetes y Soportes de PC": COMPUTER_CASE,
            "Cables de Audio y Video": None,
            "Pen Drives": USB_FLASH_DRIVE,
            "Joysticks": None,
            "Memorias": RAM,
            "Soportes para Vehiculos": None,
            "Fundas Cargadoras": CELL_ACCESORY,
            "Artículos de Bebé para Baños": None,
            "Juegos y Juguetes para Bebés": None,
            "Accesorios de Auto y Camioneta": None,
            "Audio para Vehículos": None,
            "Handies y Radiofrecuencia": None,
            "Manos Libres": None,
            "Televisores": TELEVISION,
            "Home Theater": STEREO_SYSTEM,
            "Parlantes y Subwoofers": STEREO_SYSTEM,
            "Climatización": AIR_CONDITIONER,
            "Hornos y Cocinas": OVEN,
            "Lavado": WASHING_MACHINE,
            "Refrigeración": REFRIGERATOR,
            "Refrigeradores": REFRIGERATOR,
            "Repuestos y Accesorios": None,
            "Aspiradoras": VACUUM_CLEANER,
            "Aspiradoras Robot": VACUUM_CLEANER,
            "Lavadora-Secadoras": WASHING_MACHINE,
            "Lavavajillas": DISH_WASHER,
            "Secadoras": WASHING_MACHINE,
            "Aires Acondicionados": AIR_CONDITIONER,
            "Lápices y Uñetas": None,
            "Herramientas": None,
            "Industrias y Oficinas": None,
            "Otras Categorías": None,
            "Equipaje y Accesorios de Viaje": None,
            "Mochilas": None,
            "Tratamientos Respiratorios": None,
            "Humidificadores": None,
            "Purificadores de Aire": None,
            "Lámparas": LAMP,
            "Para Cocina": None,
            "Para Hogar": None,
            "Artefactos para el Cabello": None,
            "Balanzas de Baño": None,
            "Ciclismo": None,
            "Pulsómetros y Cronómetros": None,
            "Monociclos Eléctricos": None,
            "Monopatines": None,
            "De Pie": None,
            "Eléctricos": None,
            "Cámaras": CAMERA,
            "Revelado y Laboratorio": None,
            "Antenas Wireless": None,
            "Parlantes": STEREO_SYSTEM,
            "Barbería": None,
            "Cuidado de la Piel": None,
            "Higiene Personal": None,
            "Cepillos": None,
            "Cepillos Eléctricos": None,
            "UPS": UPS,
            "Ultrabooks": NOTEBOOK,
            "Switches": None,
            "Memorias RAM": RAM,
            "Tarjetas de Red": None,
            "Impresión": PRINTER,
            "Impresoras": PRINTER,
            "Insumos de Impresión": None,
            "Cartuchos de Tinta": None,
            "Tintas": None,
            "Toners": None,
            "Repuestos": None,
            "Micrófonos": None,
            "Para Nintendo": None,
            "Headsets": HEADPHONES,
            "Docking Stations": None,
            "Maletines y Bolsos": None,
            "Filtros de Privacidad": None,
            "Soportes": None,
            "Memorias Digitales": None,
            "All In One": ALL_IN_ONE,
            "Computadores": None,
            "Mini PCs": None,
            "Repuestos para Notebooks": None,
            "Micro y Minicomponentes": STEREO_SYSTEM,
            "Consolas": VIDEO_GAME_CONSOLE,
            "Fundas y Estuches": None,
            "Audio y Video para Gaming": None,
            "Fundas para Controles": None,
            "Discos Duros y SSDs": STORAGE_DRIVE,
            "Sillas": GAMING_CHAIR,
            "Sillas Tándem": GAMING_CHAIR,
            "Otros Cables": None,
            "Soportes para Parlantes": None,
            "Baterías": None,
            "Videojuegos": VIDEO_GAME,
            "Antigüedades y Colecciones": None,
            "Lentes y Accesorios": None,
            "Llaveros": None,
            "Paraguas": None,
            "Lentes de Sol": None,
            "Ópticos": None,
            "Juegos de Agua y Playa": None,
            "Juegos de Construcción": None,
            "Juegos de Mesa y Cartas": None,
            "Juegos de Salón": None,
            "Juguetes Antiestrés e Ingenio": None,
            "Juguetes de Oficios": None,
            "Muñecos y Muñecas": None,
            "Peluches": None,
            "Figuras de Acción": None,
            "Muñecas y Bebés": None,
            "Puzzles": None,
            "Trompos": None,
            "Cartas Coleccionables R.P.G.": None,
            "Juegos de Mesa": None,
            "Pilas y Cargadores": None,
            "Video": VIDEO_CAMERA,
            "Cargadores de Pilas": None,
            "Pilas": None,
            "Amplificadores y Receivers": None,
            "Pinballs y Arcade": None,
            "PS2 - PlayStation 2": VIDEO_GAME_CONSOLE,
            "PS3 - PlayStation 3": VIDEO_GAME_CONSOLE,
            "Cargadores para Controles": None,
            "Gamepads y Joysticks": None,
            "Controles": None,
            "Skins": None,
            "Controles y Joysticks": None,
            "Game Boy Advance - GBA": VIDEO_GAME_CONSOLE,
            "Game Cube": VIDEO_GAME_CONSOLE,
            "Nintendo Switch": VIDEO_GAME_CONSOLE,
            "Nintendo Wii": VIDEO_GAME_CONSOLE,
            "Nintendo Wii U": VIDEO_GAME_CONSOLE,
            "Protectores de Pantalla": CELL_ACCESORY,
            "Cables de Red": None,
            "Cuadernos": None,
            "Estuches de Lápices": None,
            "Enfriadores de Aire": None,
            "Estufas y Calefactores": STOVE,
            "Ventiladores": None,
            "Planchas": None,
            "Hervidores": None,
            "Preparación de Alimentos": None,
            "Preparación de Bebidas": None,
            "Arroceras": None,
            "Batidoras": None,
            "Sartenes y Ollas Eléctricas": None,
            "Tostadoras": None,
            "Cocinas": STOVE,
            "Extractores y Purificadores": None,
            "Hornos": OVEN,
            "Artículos de Vino y Coctelería": None,
            "Cocción y Horneado": OVEN,
            "Utensilios de Preparación": None,
            "Vajilla y Artículos de Servir": None,
            "Bandejas": None,
            "Cuchillería": None,
            "Cuchillos de Cocina": None,
            "Juegos de Cuchillería": None,
            "Coladores y Tendederos": None,
            "Medidores de Cocina": None,
            "Baterías de Cocina": None,
            "Ollas": None,
            "Sartenes": None,
            "Balanzas de Cocina": None,
            "Máquinas para Postres": None,
            "Licuadoras": None,
            "Cafeteras": None,
            "Encimeras": None,
            "Calefonts y Termos": None,
            "Sistemas de Monitoreo": None,
            "Timbres": None,
            "Dispensadores y Purificadores": None,
            "Filtros": None,
            "Jardín y Aire Libre": None,
            "Freidoras": None,
            "Hornos de Pan": None,
            "Microondas": OVEN,
            "Cavas de Vino": None,
            "Freezers": REFRIGERATOR,
            "Almacenamiento y Organización": None,
            "Vajilla": None,
            "Fuentes": None,
            "Jarras": None,
            "Juegos de Vajilla": None,
            "Afiladores": None,
            "Moldes": None,
            "Tablas para Picar": None,
            "Bandejas, Asaderas y Fuentes": None,
            "Baterías, Ollas y Sartenes": None,
            "Vaporieras": None,
            "Para Cocinas y Hornos": None,
            "Calderas": None,
            "Chimeneas y Salamandras": None,
            "Calefonts": None,
            "Termos": None,
            "Baños": None,
            "Piscinas y Accesorios": None,
            "Spa Exterior": None,
            "Calentadores": None,
            "Limpieza y Mantenimiento": None,
            "Piscinas": None,
            "Accesorios para Baño": None,
            "Tinas": None,
            "Electricidad": None,
            "Mobiliario para Baños": None,
            "Jugueras": None,
            "Minipimers": None,
            "Parrillas Eléctricas": None,
            "Sandwicheras": None,
            "Procesadores": PROCESSOR,
            "Waffleras": None,
            "Yogurteras": None,
            "Utensilios de Repostería": None,
            "Tenedores": None,
            "Para Aires Acondicionados": AIR_CONDITIONER,
            "Para Calefont y Termos": None,
            "Gasfitería": None,
            "Mobiliario para Cocinas": None,
            "Exprimidores Eléctricos": None,
            "Mopas a Vapor": None
        }
