from .mercado_libre_chile import MercadoLibreChile
from storescraper.categories import STEREO_SYSTEM, TELEVISION, CELL_ACCESORY, \
    CELL, WEARABLE, VACUUM_CLEANER, REFRIGERATOR, AIR_CONDITIONER, OVEN, \
    WASHING_MACHINE, TABLET, DISH_WASHER, MONITOR, PROJECTOR
from ..utils import session_with_proxy


class MercadoLibreSamsung(MercadoLibreChile):
    official_store_id = 462

    @classmethod
    def categories(cls):
        return [
            STEREO_SYSTEM,
            TELEVISION,
            CELL_ACCESORY,
            CELL,
            WEARABLE,
            STEREO_SYSTEM,
            VACUUM_CLEANER,
            REFRIGERATOR,
            AIR_CONDITIONER,
            OVEN,
            WASHING_MACHINE,
            TABLET,
            PROJECTOR,
            DISH_WASHER,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        categories_codes = {
            STEREO_SYSTEM: ['MLC1010'],  # Audio
            TELEVISION: ['MLC1002'],  # Televisores
            CELL_ACCESORY: [
                'MLC3813',  # Accesorios para Celulares
                'MLC431414',  # Accesorios para TV
                'MLC179816',  # Repuestos y Accesorios (Refrigeración)
                'MLC174295',  # Extractores y Purificadores
                'MLC176937',  # Repuestos y Accesorios (Climatización)
                'MLC85756',  # Accesorios (Tablet)
            ],
            CELL: ['MLC1055'],  # Celulares y Smartphones
            WEARABLE: ['MLC417704'],  # Smartwatches y accesorios
            VACUUM_CLEANER: [
                'MLC1581',  # Pequeños electrodomésticos
            ],
            REFRIGERATOR: [
                'MLC9456',  # Refrigeradores
            ],
            AIR_CONDITIONER: [
                'MLC29800',  # Aires Acondicionados
                'MLC409431',  # Salud y Equipamiento Médico
            ],
            OVEN: [
                'MLC30854',  # Hornos
                'MLC30848',  # Microondas
            ],
            DISH_WASHER: ['MLC174300'],  # Lavavajillas
            WASHING_MACHINE: [
                'MLC178593',  # Lavadora-Secadoras
            ],
            TABLET: [
                'MLC82067',  # Tablets
            ],
            MONITOR: [
                'MLC1655',  # Monitores y Accesorios
            ],
            PROJECTOR: [
                'MLC9239',  # Proyectores y Telones
                'MLC1657',  # Proyectores y Telones
            ],

        }
        session = session_with_proxy(extra_args)
        product_urls = []
        for category_code in categories_codes[category]:
            product_urls.extend(
                cls.get_products(session, category, category_code,
                                 official_store_id=cls.official_store_id))

        # Sanity check, verify that we are getting all products
        # all_products = cls.get_products(
        #     session, official_store_id=cls.official_store_id)
        #
        # for url in all_products:
        #     assert url in product_urls, url

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        # Remove the seller because we consider MecadoLibreSamsung to be a
        # standalone retailer, in particular because the Samsung WTB system
        # only displays entries without a seller (not from marketplaces)
        # and we want to consider MercadoLibreSamsung for that.
        products = super().products_for_url(
            url, category=category, extra_args=extra_args)

        filtered_products = []

        for product in products:
            assert product.seller
            product.seller = None
            filtered_products.append(product)

        return filtered_products
