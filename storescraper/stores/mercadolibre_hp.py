from storescraper.stores.mercadolibre_chile import MercadolibreChile


class MercadolibreHp(MercadolibreChile):
    store_extension = '_Tienda_hp'

    @classmethod
    def _category_paths(cls):
        return [
            ('computacion/notebooks', 'Notebook'),
            ('pc-escritorio', 'AllInOne'),
            ('computacion/impresoras/impresoras', 'Printer'),
            ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
            # No idea why the all in ones are in almacenamiento
            ('almacenamiento', 'AllInOne'),
            ('monitores-accesorios', 'Monitor'),
        ]
