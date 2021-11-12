from .lg_v5 import LgV5


class LgChile(LgV5):
    region_code = 'cl'
    currency = 'CLP'

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
            'CellAccesory',
            'Notebook',
            'OpticalDrive',
            'B2B',
            'Headphones',
            'Stove',
            'AirConditioner'
        ]

    @classmethod
    def _category_paths(cls):
        return [
            # Televisores
            ('CT20106005', 'Television', True),
            ('CT20106005', 'Television', False),
            # Video
            ('CT20106017', 'OpticalDiskPlayer', False),
            ('CT20106019', 'OpticalDiskPlayer', True),
            # Equipos de música
            ('CT20106020', 'StereoSystem', True),
            ('CT20106020', 'StereoSystem', False),
            # Minicomponentes
            ('CT20106021', 'StereoSystem', True),
            ('CT20106021', 'StereoSystem', False),
            # Audio portable
            ('CT40005301', 'StereoSystem', True),
            ('CT40005301', 'StereoSystem', False),
            # Sound bar
            ('CT40005303', 'StereoSystem', True),
            ('CT40005303', 'StereoSystem', False),
            # Audífonos
            ('CT30011860', 'Headphones', True),
            ('CT30011860', 'Headphones', False),
            # Audio Hi-Fi
            ('CT30016640', 'StereoSystem', True),
            ('CT30016640', 'StereoSystem', False),
            # Celulares (code sale en la vista de descontinuados)
            ('CT20106027', 'Cell', True),
            ('CT20106027', 'Cell', False),
            # Refrigeradores
            ('CT20106034', 'Refrigerator', True),
            ('CT20106034', 'Refrigerator', False),
            # Secadoras
            ('CT20106044', 'WashingMachine', True),
            ('CT20106044', 'WashingMachine', False),
            # Lavadoras
            ('CT20106040', 'WashingMachine', True),
            ('CT20106040', 'WashingMachine', False),
            # Microondas
            ('CT20106039', 'Oven', True),
            ('CT20106039', 'Oven', False),
            # Monitores
            ('CT20106054', 'Monitor', True),
            ('CT20106054', 'Monitor', False),
            # Proyectores
            ('CT30006480', 'Projector', True),
            ('CT30006480', 'Projector', False),

            # Desaparecidos de la navegacion pero aun con
            # urls validas en LG.com

            # LG Friends (accesorios LG G5 SE)
            # ('CT31903594', 'CellAccesory', True),
            # Aspiradoras
            # ('CT20106045', 'VacuumCleaner', False),
            # Computador All In One
            # ('CT30018920', 'AllInOne', True),
            # Notebooks
            # ('CT32002362', 'Notebook', True),
            # Grabadores Blu-Ray DVD
            # ('CT20106055', 'OpticalDrive', True),
            # ('CT20106055', 'OpticalDrive', False),
        ]
