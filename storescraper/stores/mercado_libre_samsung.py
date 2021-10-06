from .mercado_libre_chile import MercadoLibreChile
from storescraper.categories import STEREO_SYSTEM, TELEVISION, CELL_ACCESORY, \
    CELL, WEARABLE, VACUUM_CLEANER, REFRIGERATOR, AIR_CONDITIONER, OVEN, \
    WASHING_MACHINE, TABLET, DISH_WASHER, MONITOR
from ..utils import session_with_proxy


class MercadoLibreSamsung(MercadoLibreChile):
    seller_id = '404495030'

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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        categories_codes = {
            STEREO_SYSTEM: ['MLC1012', 'MLC10177', 'MLC1022'],
            TELEVISION: ['MLC1002'],
            CELL_ACCESORY: ['MLC3813', 'MLC431414', 'MLC85756'],
            CELL: ['MLC1055'],
            WEARABLE: ['MLC417704'],
            VACUUM_CLEANER: ['MLC4337', 'MLC180993', 'MLC455108'],
            REFRIGERATOR: ['MLC9456', 'MLC179816'],
            AIR_CONDITIONER: ['MLC29800', 'MLC176937', 'MLC409431'],
            OVEN: ['MLC1580'],
            DISH_WASHER: ['MLC174300'],
            WASHING_MACHINE: ['MLC178593', 'MLC27590'],
            TABLET: ['MLC82067'],
            MONITOR: ['MLC1655']
        }
        session = session_with_proxy(extra_args)
        product_urls = []
        for category_code in categories_codes[category]:
            super().get_products(session, category, category_code,
                                 product_urls, cls.seller_id)

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

            # For some reason other SKUs may get mingled with official stores,
            # so skip those
            if 'SAMSUNG' in product.seller.upper():
                product.seller = None
                filtered_products.append(product)

        return filtered_products
