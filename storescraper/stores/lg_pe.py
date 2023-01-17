from .lg_v5 import LgV5
from storescraper.categories import TELEVISION, OPTICAL_DISK_PLAYER, \
    STEREO_SYSTEM, HEADPHONES, REFRIGERATOR, WASHING_MACHINE, OVEN, \
    MONITOR, STOVE, ALL_IN_ONE, \
    NOTEBOOK, OPTICAL_DRIVE, AIR_CONDITIONER


class LgPe(LgV5):
    region_code = 'pe'
    currency = 'PEN'
    price_approximation = '0.01'

    @classmethod
    def _category_paths(cls):
        return [
            # Televisores
            ('CT20190005', TELEVISION, True),
            ('CT20190005', TELEVISION, False),
            # TVs LIFESTYLE
            ('CT40016301', TELEVISION, True),
            ('CT40016301', TELEVISION, False),
            # Equipos de sonido
            ('CT20190015', STEREO_SYSTEM, True),
            ('CT20190015', STEREO_SYSTEM, False),
            # AUDÍFONOS
            ('CT40010303', HEADPHONES, True),
            ('CT40010303', HEADPHONES, False),
            # Video (DVD / BLU-RAY)
            ('CT20190011', OPTICAL_DISK_PLAYER, True),
            ('CT20190011', OPTICAL_DISK_PLAYER, False),
            # Refrigeradoras
            ('CT20190033', REFRIGERATOR, True),
            ('CT20190033', REFRIGERATOR, False),
            # Lavadoras
            ('CT20190041', WASHING_MACHINE, True),
            ('CT20190041', WASHING_MACHINE, False),
            # Microondas
            ('CT20190038', OVEN, True),
            ('CT20190038', OVEN, False),
            # Cocinas
            ('CT32002801', STOVE, True),
            ('CT32002801', STOVE, False),
            # All in one
            ('CT30018781', ALL_IN_ONE, True),
            ('CT30018781', ALL_IN_ONE, False),
            # LG gram
            ('CT32001321', NOTEBOOK, True),
            ('CT32001321', NOTEBOOK, False),
            # Monitores
            ('CT20190057', MONITOR, True),
            ('CT20190057', MONITOR, False),
            # Almacenamiento Óptico
            ('CT20190064', OPTICAL_DRIVE, True),
            ('CT20190064', OPTICAL_DRIVE, False),
            # PANTALLAS COMERCIALES
            ('CT40015395', MONITOR, True),
            ('CT40015395', MONITOR, False),
            # Aire Acondicionado Residencial
            ('CT20190086', AIR_CONDITIONER, True),
            ('CT20190086', AIR_CONDITIONER, False),
            # Aire acondicionado comercial
            ('CT20190090', AIR_CONDITIONER, True),
            ('CT20190090', AIR_CONDITIONER, False),
        ]
