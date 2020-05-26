from storescraper.stores.mercadolibre_chile import MercadolibreChile


class MercadolibreMotorola(MercadolibreChile):
    store_extension = '_Tienda_motorola'

    @classmethod
    def _category_paths(cls):
        return [
            ('audio', 'Headphones'),
            ('celulares-telefonia/celulares', 'Cell'),
            ('celulares-telefonia/accesorios-celulares', 'StereoSystem'),
        ]
