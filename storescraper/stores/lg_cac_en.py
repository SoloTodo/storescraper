from .lg_v5 import LgV5


class LgCacEn(LgV5):
    region_code = 'cac_en'

    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Projector',
            'Cell',
            'Refrigerator',
            'Oven',
            'WashingMachine',
            'VacuumCleaner',
            'Monitor',
            'CellAccesory',
            'Notebook',
            'Headphones',
            'Stove',
            'AirConditioner',
            'DishWasher'
        ]

    @classmethod
    def _category_paths(cls):
        return [
            # Todos los Televisores
            ('CT20273031', 'Television', True),
            ('CT20273031', 'Television', False),
            # Proyectores
            ('CT20273021', 'Projector', True),
            ('CT20273021', 'Projector', False),
            # Equipos de sonido
            ('CT20273041', 'StereoSystem', True),
            ('CT20273041', 'StereoSystem', False),
            # Audífonos inalámbricos
            ('CT40001005', 'Headphones', True),
            ('CT40001005', 'Headphones', False),
            # Teléfonos Celulares
            ('CT20273028', 'Cell', True),
            ('CT20273028', 'Cell', False),
            # Refrigeradora
            ('CT20273018', 'Refrigerator', True),
            ('CT20273018', 'Refrigerator', False),
            # Estufa
            ('CT30015280', 'Stove', True),
            ('CT30015280', 'Stove', False),
            # Microondas
            ('CT20273007', 'Oven', True),
            ('CT20273007', 'Oven', False),
            # Campanas (consideradas como accesorios)
            ('CT32021843', 'CellAccesory', True),
            # Lavaplatos
            ('CT30015421', 'DishWasher', True),
            # Lavadoras y secadoras
            ('CT20273012', 'WashingMachine', True),
            ('CT20273012', 'WashingMachine', False),
            # Styler
            ('CT32015122', 'WashingMachine', True),
            # Aspiradoras
            ('CT20273011', 'VacuumCleaner', True),
            ('CT20273011', 'VacuumCleaner', False),
            # Aire acondicionado residencial
            ('CT30014260', 'AirConditioner', True),
            ('CT30014260', 'AirConditioner', False),
            # Monitores
            ('CT20273024', 'Monitor', True),
            ('CT20273024', 'Monitor', False),
            # Laptops
            ('CT40006155', 'Notebook', True),
            # LG Studio
            ('CT32021982', 'Stove', True),
            ('CT32021982', 'Stove', False),
        ]
