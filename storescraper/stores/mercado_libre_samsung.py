from .mercado_libre_chile import MercadoLibreChile
from storescraper.categories import STEREO_SYSTEM, TELEVISION, CELL_ACCESORY, \
    CELL, WEARABLE, VACUUM_CLEANER, REFRIGERATOR, AIR_CONDITIONER, STOVE, OVEN, \
    WASHING_MACHINE, TABLET


class MercadoLibreSamsung(MercadoLibreChile):
    store_extension = '_Tienda_samsung'

    @classmethod
    def _category_paths(cls):
        return {'_Tienda_samsung': [
            ('audio', STEREO_SYSTEM),
            ('electronica/televisores', TELEVISION),
            ('accesorios-tv', CELL_ACCESORY),
            ('celulares-telefonia/accesorios-celulares', CELL_ACCESORY),
            ('celulares-telefonia/celulares', CELL),
            ('smartwatches-accesorios', WEARABLE),
            ('handies-radiofrecuencia', STEREO_SYSTEM),
            ('electrodomesticos/pequenos', VACUUM_CLEANER),
            ('electrodomesticos/refrigeracion', REFRIGERATOR),
            ('electrodomesticos/climatizacion/aires-acondicionados',
             AIR_CONDITIONER),
            ('climatizacion-repuestos-accesorios', CELL_ACCESORY),
            ('electrodomesticos/hornos-cocinas/encimeras', STOVE),
            ('electrodomesticos/hornos-cocinas/microondas', OVEN),
            ('electrodomesticos/hornos-cocinas/extractores-purificadores',
             CELL_ACCESORY),
            ('lavado', WASHING_MACHINE),
            ('computacion/tablets', TABLET),
            ('computacion/tablets/accesorios', CELL_ACCESORY),
            ('salud-equipamiento-medico', AIR_CONDITIONER),
            ('fotografia', CELL_ACCESORY),
        ]}

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
