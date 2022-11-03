from storescraper.categories import WATER_HEATER, OVEN, DISH_WASHER, \
    REFRIGERATOR, WASHING_MACHINE, VACUUM_CLEANER, NOTEBOOK, ALL_IN_ONE, \
    MONITOR, EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, PRINTER, TABLET, MOUSE, \
    KEYBOARD, GAMING_CHAIR, HEADPHONES, COMPUTER_CASE, CELL, TELEVISION, \
    VIDEO_GAME_CONSOLE, STEREO_SYSTEM, AIR_CONDITIONER, SPACE_HEATER
from .falabella import Falabella


class Sodimac(Falabella):
    store_and_subdomain = 'sodimac'
    seller = 'SODIMAC'

    category_paths = [
        ['cat2013', [WATER_HEATER],
         'Home > Sodimac > Cocina y Baño-Baño > Calefont y Termos', 1],
        ['cat4054', [OVEN],
         'Home > Sodimac > Electrohogar-Línea blanca > Cocina > '
         'Hornos Empotrables', 1],
        ['cat3151', [OVEN],
         'Home > Sodimac > Electrohogar-Electrodomésticos Cocina > '
         'Microondas', 1],
        ['CATG10013', [DISH_WASHER],
         'Home > Sodimac > Cocina y Baño-Cocina > Lavaplatos', 1],
        ['CATG19018', [REFRIGERATOR],
         'Home > Sodimac > Electrohogar-Línea blanca > Refrigeración', 1],
        ['cat3136', [WASHING_MACHINE],
         'Home > Sodimac > Electrohogar-Línea blanca > Lavado', 1],
        ['cat3025', [VACUUM_CLEANER],
         'Home > Sodimac > Electrohogar-Aspirado y Limpieza > Aspiradoras', 1],
        ['cat70057', [NOTEBOOK],
         'Home > Sodimac > Tecnología-Computadores > Notebooks', 1],
        ['cat40051', [ALL_IN_ONE],
         'Home > Sodimac > Tecnología-Computadores > All in one', 1],
        ['cat2062', [MONITOR],
         'Home > Sodimac > Tecnología-Computadores > Monitores', 1],
        ['cat3087', [EXTERNAL_STORAGE_DRIVE],
         'Home > Sodimac > Tecnología-Computadores > Almacenamiento > '
         'Discos duros', 1],
        ['cat3177', [USB_FLASH_DRIVE],
         'Home > Sodimac > Tecnología-Computadores > Almacenamiento > '
         'Discos duros', 1],
        ['cat1820004', [PRINTER],
         'Home > Sodimac > Tecnología-Computadores > Impresoras > '
         'Impresoras', 1],
        ['cat7230007', [TABLET],
         'Home > Sodimac > Tecnología-Computadores > Tablets', 1],
        ['cat3155', [MOUSE],
         'Home > Sodimac > Tecnología-Computadores > Accesorios Computación > '
         'Mouse', 1],
        ['cat2370002', [KEYBOARD],
         'Home > Sodimac > Tecnología-Computadores > Accesorios Computación > '
         'Mouse', 1],
        ['CATG19007', [MOUSE],
         'Home > Sodimac > Tecnología-Computadores > Accesorios gamer > '
         'Mouse gamer', 1],
        ['CATG19011', [GAMING_CHAIR],
         'Home > Sodimac > Tecnología-Computadores > Accesorios gamer > '
         'Sillas gamer', 1],
        ['CATG19008', [KEYBOARD],
         'Home > Sodimac > Tecnología-Computadores > Accesorios gamer > '
         'Teclados gamer', 1],
        ['cat4930009', [HEADPHONES],
         'Home > Sodimac > Tecnología-Computadores > Accesorios gamer > '
         'Audífonos gamer', 1],
        ['cat13520029', [MOUSE],
         'Home > Sodimac > Tecnología-Computadores > Accesorios gamer > '
         'Componentes gamer', 1],
        ['CATG19012', [COMPUTER_CASE],
         'Home > Sodimac > Tecnología-Computadores > Accesorios gamer > '
         'Gabinete gamer', 1],
        ['cat2018', [CELL], 'Home > Sodimac > Tecnología-Telefonía > '
                            'Celulares y Teléfonos', 1],
        ['cat7190148', [TELEVISION],
         'Home > Sodimac > tecnología-TV y Video > Smart TV', 1],
        ['cat202303', [VIDEO_GAME_CONSOLE],
         'Home > Sodimac > Tecnología-Videojuegos > Consolas', 1],
        ['cat2005', [STEREO_SYSTEM], 'Home > Sodimac > Tecnología-Audio', 1],
        ['cat7830014', [AIR_CONDITIONER],
         'Home > Sodimac > Electrohogar-Climatización > Aire acondicionado > '
         'Split', 1],
        ['cat7830015', [AIR_CONDITIONER],
         'Home > Sodimac > Electrohogar-Climatización > Aire acondicionado > '
         'Portátiles', 1],
        ['CATG10178', [SPACE_HEATER],
         'Home > Sodimac > Electrohogar-Climatización > Calefacción > '
         'Estufas', 1],
        ['cat13490034', [STEREO_SYSTEM],
         'Home > Sodimac > Tecnología-Smart Home > Asistentes por Voz', 1],
    ]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super().products_for_url(url, category=category,
                                            extra_args=extra_args)

        for product in products:
            product.url = url
            product.discovery_url = url
            if product.seller and product.seller.upper() == 'SODIMAC':
                product.seller = None

        return products
