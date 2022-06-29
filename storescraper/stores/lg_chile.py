from .lg_v5 import LgV5
from storescraper.categories import TELEVISION, OPTICAL_DISK_PLAYER, \
    STEREO_SYSTEM, HEADPHONES, CELL, REFRIGERATOR, WASHING_MACHINE, OVEN, \
    MONITOR, PROJECTOR, CELL_ACCESORY


class LgChile(LgV5):
    region_code = 'cl'
    currency = 'CLP'

    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            OPTICAL_DISK_PLAYER,
            STEREO_SYSTEM,
            PROJECTOR,
            CELL,
            REFRIGERATOR,
            OVEN,
            WASHING_MACHINE,
            MONITOR,
            HEADPHONES,
            CELL_ACCESORY
        ]

    @classmethod
    def _category_paths(cls):
        return [
            # Televisores
            ('CT20106005', TELEVISION, True),
            ('CT20106005', TELEVISION, False),
            # Video
            ('CT20106017', OPTICAL_DISK_PLAYER, False),
            ('CT20106019', OPTICAL_DISK_PLAYER, True),
            # Equipos de música
            ('CT40012703', STEREO_SYSTEM, True),
            ('CT40012703', STEREO_SYSTEM, False),
            # Minicomponentes
            ('CT40012705', STEREO_SYSTEM, True),
            ('CT40012705', STEREO_SYSTEM, False),
            # Audio portable
            ('CT40012723', STEREO_SYSTEM, True),
            ('CT40012723', STEREO_SYSTEM, False),
            # Sound bar
            ('CT40012725', STEREO_SYSTEM, True),
            ('CT40012725', STEREO_SYSTEM, False),
            # Audífonos
            ('CT40012727', HEADPHONES, True),
            ('CT40012727', HEADPHONES, False),
            # Audífonos con UV Nano
            ('CT40012729', HEADPHONES, True),
            ('CT40012729', HEADPHONES, False),
            # Accesorios de audio
            ('CT40013665', STEREO_SYSTEM, True),
            ('CT40013665', STEREO_SYSTEM, False),
            # Celulares (code sale en la vista de descontinuados)
            ('CT20106027', CELL, True),
            ('CT20106027', CELL, False),
            # Refrigeradores
            ('CT20106034', REFRIGERATOR, True),
            ('CT20106034', REFRIGERATOR, False),
            # Secadoras
            ('CT20106044', WASHING_MACHINE, True),
            ('CT20106044', WASHING_MACHINE, False),
            # Lavadoras
            ('CT20106040', WASHING_MACHINE, True),
            ('CT20106040', WASHING_MACHINE, False),
            # Microondas
            ('CT20106039', OVEN, True),
            ('CT20106039', OVEN, False),
            # Monitores
            ('CT20106054', MONITOR, True),
            ('CT20106054', MONITOR, False),
            # Proyectores
            ('CT30006480', PROJECTOR, True),
            ('CT30006480', PROJECTOR, False),
            # Styler
            ('CT40013711', CELL_ACCESORY, True),
        ]
