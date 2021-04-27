from .lg_v5 import LgV5


class LgEc(LgV5):
    region_code = 'ec'

    @classmethod
    def categories(cls):
        return [
            'Television',
            'OpticalDiskPlayer',
            'StereoSystem',
            'Projector',
            'Cell',
            'Refrigerator',
            'Oven',
            'WashingMachine',
            'VacuumCleaner',
            'Monitor',
            'Stove',
            'AirConditioner',
        ]

    @classmethod
    def _category_paths(cls):
        return [
            # Todos los Televisores
            ('CT20281031', 'Television', True),
            ('CT20281031', 'Television', False),
            # Audio
            ('CT20281041', 'StereoSystem', True),
            ('CT20281041', 'StereoSystem', False),
            # Video
            ('CT20281047', 'OpticalDiskPlayer', True),
            ('CT20281047', 'OpticalDiskPlayer', False),
            # Proyectores
            ('CT30017660', 'Projector', True),
            # Teléfonos Celulares
            ('CT20281028', 'Cell', True),
            ('CT20281028', 'Cell', False),
            # Refrigeradora
            ('CT20281018', 'Refrigerator', True),
            ('CT20281018', 'Refrigerator', False),
            # Microondas
            ('CT20281007', 'Oven', True),
            ('CT20281007', 'Oven', False),
            # Aspiradoras
            ('CT20281011', 'VacuumCleaner', True),
            # ('CT20281011', 'VacuumCleaner', False),
            # Lavadoras y secadoras
            ('CT20281012', 'WashingMachine', True),
            ('CT20281012', 'WashingMachine', False),
            # Styler
            ('CT32014262', 'WashingMachine', True),
            # Cocinas
            ('CT32008902', 'Stove', True),
            # ('CT32008902', 'Stove', False),
            # Aire acondicionado residencial
            ('CT30006200', 'AirConditioner', True),
            ('CT30006200', 'AirConditioner', False),
            # Purificadores de aire
            ('CT40006995', 'AirConditioner', True),
            # Monitores
            ('CT20281024', 'Monitor', True),
            ('CT20281024', 'Monitor', False),
        ]
