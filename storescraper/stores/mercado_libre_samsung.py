from .mercado_libre_chile import MercadoLibreChile


class MercadoLibreSamsung(MercadoLibreChile):
    store_extension = '_Tienda_samsung'

    @classmethod
    def _category_paths(cls):
        return {'_Tienda_samsung': [
            ('electrodomesticos/pequenos', 'VacuumCleaner'),
            ('electrodomesticos/refrigeracion', 'Refrigerator'),
            ('lavado', 'WashingMachine'),
            ('electrodomesticos/climatizacion', 'AirConditioner'),
            ('electrodomesticos/hornos-cocinas', 'Oven'),
            ('celulares-telefonia/celulares', 'Cell'),
            ('celulares-telefonia/accesorios-celulares', 'CellAccesory'),
            ('smartwatches-accesorios', 'Wearable'),
            ('audio', 'Headphones'),
            ('electronica/televisores', 'Television'),
            ('accesorios-tv', 'CellAccesory'),
            ('relojes-joyas', 'Wearable'),
            ('computacion', 'Tablet'),
            ('instrumentos', 'StereoSystem'),
            # Invalid as of 2020-10-20
            ('repuestos-accesorios', 'CellAccesory'),
            ('accesorios-audio-video', 'CellAccesory'),
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
