from storescraper.categories import CELL
from .movistar import Movistar


class MovistarOne(Movistar):
    cell_catalog_suffix = '&movistarone=1'
    aquisition_options = [
        # Línea nueva sin arriendo
        (3, 3, ''),
        # Portabilidad sin arriendo
        (1, 3, ' Portabilidad'),
    ]

    @classmethod
    def categories(cls):
        return [
            CELL
        ]
