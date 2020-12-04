from .mercado_libre_chile import MercadoLibreChile


class MercadoLibreLg(MercadoLibreChile):
    store_extension = '_Tienda_lg'

    @classmethod
    def _category_paths(cls):
        return {'_Tienda_lg': [
            ('audio', 'StereoSystem'),
            ('electronica/televisores', 'Television'),
            ('electrodomesticos/refrigeracion', 'Refrigerator'),
            ('lavado', 'WashingMachine'),
        ]}

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
