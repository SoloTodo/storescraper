from storescraper.categories import CELL
from .movistar import Movistar


class MovistarOne(Movistar):
    requires_movistar_one = True
    variations = [{
        'base_plan': 'EMP_NUM_MOV_5GLibreUltraAltasPar',
        'methods': [
            (3, ' Cuotas'),
        ]
    },
        {
            'base_plan': 'EMP_POR_MOV_5GLibreUltraPortaPar',
            'methods': [
                (3, ' Portabilidad Cuotas'),
            ]}
    ]

    @classmethod
    def categories(cls):
        return [
            CELL
        ]
