from storescraper.categories import CELL
from .movistar import Movistar


class MovistarOne(Movistar):
    variations = [{
        'base_plan': 'skuLineaNuevaTienda',
        'methods': [
            (3, ' Cuotas'),
        ]
    },
        {
            'base_plan': 'skuPortabilidadTienda',
            'methods': [
                (3, ' Portabilidad Cuotas'),
            ]}
    ]
    include_prepago = False

    @classmethod
    def categories(cls):
        return [
            CELL
        ]
