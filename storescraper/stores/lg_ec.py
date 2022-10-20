from .lg_v5 import LgV5
from ..categories import TELEVISION, STEREO_SYSTEM, OPTICAL_DISK_PLAYER, \
    PROJECTOR, CELL, REFRIGERATOR, OVEN, VACUUM_CLEANER, WASHING_MACHINE, \
    STOVE, AIR_CONDITIONER, MONITOR


class LgEc(LgV5):
    region_code = 'ec'

    @classmethod
    def _category_paths(cls):
        return [
            # Todos los Televisores
            ('CT20281031', TELEVISION, True),
            ('CT20281031', TELEVISION, False),
            # Audio
            ('CT20281041', STEREO_SYSTEM, True),
            ('CT20281041', STEREO_SYSTEM, False),
            # Video
            ('CT20281047', OPTICAL_DISK_PLAYER, True),
            ('CT20281047', OPTICAL_DISK_PLAYER, False),
            # Proyectores
            ('CT30017660', PROJECTOR, True),
            # Teléfonos Celulares
            ('CT20281028', CELL, True),
            ('CT20281028', CELL, False),
            # Refrigeradora
            ('CT20281018', REFRIGERATOR, True),
            ('CT20281018', REFRIGERATOR, False),
            # Microondas
            ('CT20281007', OVEN, True),
            ('CT20281007', OVEN, False),
            # Aspiradoras
            ('CT40013843', VACUUM_CLEANER, True),
            # ('CT20281011', 'VacuumCleaner', False),
            # Lavadoras y secadoras
            ('CT20281012', WASHING_MACHINE, True),
            ('CT20281012', WASHING_MACHINE, False),
            # Styler
            ('CT32014262', WASHING_MACHINE, True),
            # Cocinas
            ('CT32008902', STOVE, True),
            # ('CT32008902', 'Stove', False),
            # Aire acondicionado residencial
            ('CT30006200', AIR_CONDITIONER, True),
            ('CT30006200', AIR_CONDITIONER, False),
            # Purificadores de aire
            ('CT40006995', AIR_CONDITIONER, True),
            # Monitores
            ('CT20281024', MONITOR, True),
            ('CT20281024', MONITOR, False),
        ]
