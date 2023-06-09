from .mercado_libre_chile import MercadoLibreChile
from ..categories import STEREO_SYSTEM, TELEVISION, REFRIGERATOR, \
    WASHING_MACHINE, CELL, MONITOR, CELL_ACCESORY
from ..utils import session_with_proxy


class MercadoLibreLg(MercadoLibreChile):
    official_store_id = 51202

    @classmethod
    def categories(cls):
        return [
            STEREO_SYSTEM,
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        categories_codes = {
            STEREO_SYSTEM: ['MLC1010'],
            TELEVISION: ['MLC1002'],
        }
        session = session_with_proxy(extra_args)
        product_urls = []
        for category_code in categories_codes[category]:
            product_urls.extend(
                cls.get_products(session, category, category_code,
                                 official_store_id=cls.official_store_id))

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        # Remove the seller because we consider MecadoLibreLg to be a
        # standalone retailer, in particular because the LG WTB system
        # only displays entries without a seller (not from marketplaces)
        # and we want to consider MercadoLibreLG for that.
        products = super().products_for_url(
            url, category=category, extra_args=extra_args)

        for product in products:
            product.seller = None

        return products
