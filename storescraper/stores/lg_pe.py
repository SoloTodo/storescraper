from .lg_v6 import LgV6
from storescraper.categories import (TELEVISION, STEREO_SYSTEM, REFRIGERATOR,
                                     WASHING_MACHINE, OVEN, MONITOR, STOVE,
                                     ALL_IN_ONE, NOTEBOOK, AIR_CONDITIONER)


class LgPe(LgV6):
    region_code = 'PE'
    currency = 'PEN'
    price_approximation = '0.01'

    @classmethod
    def _category_paths(cls):
        return [
            # To do TV y Soundbars
            ('CT52006227', TELEVISION),
            # Object collection Pose
            ('CT52006483', TELEVISION),
            # Flex
            ('CT52006243', TELEVISION),
            # StandbyMe Go
            ('CT52006484', TELEVISION),
            # To do equipos de sonido
            ('CT52006251', STEREO_SYSTEM),
            # Refrigeradoras French Door
            ('CT52006489', REFRIGERATOR),
            # Refrigeradoras Side by Side
            ('CT52006491', REFRIGERATOR),
            # Refrigeradoras Bottom Freezer
            ('CT52006492', REFRIGERATOR),
            # Refrigeradoras Top Freezer
            ('CT52006493', REFRIGERATOR),
            # Washtower
            ('CT52006285', WASHING_MACHINE),
            # Lavadoras Carga Frontal
            ('CT52006494', WASHING_MACHINE),
            # Lavadoras Carga Superior
            ('CT52006495', WASHING_MACHINE),
            # Secadoras de Ropa
            ('CT52006279', WASHING_MACHINE),
            # Microondas sin dorador
            ('CT52006496', OVEN),
            # Microondas con dorador
            ('CT52006342', OVEN),
            # Cocinas
            ('CT52006346', STOVE),
            # Monitores
            ('CT52006419', MONITOR),
            # All in One
            ('CT52006446', ALL_IN_ONE),
            # Laptops
            ('CT52006430', NOTEBOOK),
            # Pantallas comerciales
            ('CT52006441', TELEVISION),
            # To do aire acondicionado residencial
            ('CT52006359', AIR_CONDITIONER),
            # Aire acondicionado comercial
            ('CT52006407', AIR_CONDITIONER),
        ]
