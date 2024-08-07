from .lg_v5 import LgV5


class LgCac(LgV5):
    region_code = "cac"

    @classmethod
    def _category_paths(cls):
        return [
            # Todos los Televisores
            ("CT20188038", "Television", True),
            ("CT20188038", "Television", False),
            # Proyectores
            ("CT20188025", "Projector", True),
            ("CT20188025", "Projector", False),
            # Equipos de sonido
            ("CT40018517", "StereoSystem", True),
            ("CT40018517", "StereoSystem", False),
            # Video
            ("CT20188055", "OpticalDiskPlayer", True),
            ("CT20188055", "OpticalDiskPlayer", False),
            # Teléfonos Celulares
            ("CT20188032", "Cell", True),
            ("CT20188032", "Cell", False),
            # Audífonos
            ("CT40011643", "Headphones", True),
            ("CT40011643", "Headphones", False),
            # Refrigeradora
            ("CT20188021", "Refrigerator", True),
            ("CT20188021", "Refrigerator", False),
            # Estufa
            ("CT30015260", "Stove", True),
            ("CT30015260", "Stove", False),
            # Microondas
            ("CT20188009", "Oven", True),
            ("CT20188009", "Oven", False),
            # Campanas (consideradas como accesorios)
            ("CT32021842", "CellAccesory", True),
            # Lavaplatos
            ("CT30015420", "DishWasher", True),
            # Lavadoras y secadoras
            ("CT20188014", "WashingMachine", True),
            ("CT20188014", "WashingMachine", False),
            # Styler
            ("CT32015142", "WashingMachine", True),
            # Aspiradoras
            ("CT20188013", "VacuumCleaner", True),
            ("CT20188013", "VacuumCleaner", False),
            # Aire acondicionado residencial
            ("CT30014140", "AirConditioner", True),
            ("CT30014140", "AirConditioner", False),
            # Deshumidificador
            # ('CT32021782', 'AirConditioner', True),
            # Monitores
            ("CT20188028", "Monitor", True),
            ("CT20188028", "Monitor", False),
            # Dispositivos ópticos
            ("CT20188024", "Monitor", True),
            ("CT20188024", "Monitor", False),
            # LG Studio
            ("CT32021962", "Stove", True),
        ]
