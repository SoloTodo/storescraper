from .mercado_libre_chile import MercadoLibreChile


class MercadoLibreSamsung(MercadoLibreChile):
    store_extension = '_Tienda_samsung'

    @classmethod
    def _category_paths(cls):
        return {'_Tienda_samsung': [
            ('electrodomesticos/pequenos', 'VacuumCleaner'),
            ('electrodomesticos/refrigeracion', 'Refrigerator'),
            ('electrodomesticos/lavado', 'WashingMachine'),
            ('electrodomesticos/climatizacion', 'AirConditioner'),
            ('repuestos-accesorios', 'CellAccesory'),
            ('electrodomesticos/hornos-cocinas', 'Oven'),
            ('celulares-telefonia/celulares', 'Cell'),
            ('celulares-telefonia/accesorios-celulares', 'CellAccesory'),
            ('smartwatches-accesorios', 'Wearable'),
            ('audio', 'Headphones'),
            ('electronica/televisores', 'Television'),
            ('accesorios-tv', 'CellAccesory'),
            ('accesorios-audio-video', 'CellAccesory'),
            ('relojes-joyas', 'Wearable'),
            ('computacion', 'Tablet'),
            ('instrumentos', 'StereoSystem'),
        ]}

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        # Remove the seller because we consider MecadoLibreSamsung to be a
        # standalone retailer, in particular because the Samsung WTB system
        # only displays entries without a seller (not from marketplaces)
        # and we want to consider MercadoLibreSamsung for that.
        products = super().products_for_url(
            url, category=category, extra_args=extra_args)

        for product in products:
            product.seller = None

        return products
