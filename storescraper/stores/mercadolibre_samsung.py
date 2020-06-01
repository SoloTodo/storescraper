from .mercadolibre_chile import MercadolibreChile


class MercadolibreSamsung(MercadolibreChile):
    store_extension = '_Tienda_samsung'

    @classmethod
    def _category_paths(cls):
        return {'_Tienda_samsung': [
            # ('electrodomesticos/pequenos', 'VacuumCleaner'),
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
            # ('accesorios-audio-video', 'CellAccesory'),
            ('relojes-joyas', 'Wearable'),
            ('computacion', 'Tablet'),
            ('instrumentos', 'StereoSystem'),
        ]}
