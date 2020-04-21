from .linio import Linio


class LinioChile(Linio):
    base_domain = 'https://www.linio.cl'
    currency = 'CLP'

    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Cell',
            'Television',
            'Tablet',
            'Printer',
            'VideoGameConsole',
            'Refrigerator',
            'WashingMachine',
            'Oven',
            'VacuumCleaner',
            'ExternalStorageDrive',
            'Keyboard',
            'Mouse',
            'AllInOne',
            'Monitor',
        ]

    @classmethod
    def _category_paths(cls):
        return [
            ['computacion/pc-portatil', 'Notebook'],
            # ['zona-gamer/notebook-gamer', 'Notebook'],
            ['celulares-y-smartphones/liberados', 'Cell'],
            ['tv-y-video/televisores/', 'Television'],
            # ['tv-audio-y-foto/', 'Television'],
            ['tablets/tablet', 'Tablet'],
            ['impresoras-y-scanners/impresoras', 'Printer'],
            ['impresoras/impresoras-laser', 'Printer'],
            ['impresoras-y-scanners/multifuncionales', 'Printer'],
            ['nintendo-videojuegos/consolas-nintendo/', 'VideoGameConsole'],
            ['playstation-videojuegos/consolas-playstation/',
             'VideoGameConsole'],
            ['xbox-videojuegos/consolas-xbox/', 'VideoGameConsole'],
            ['refrigeracion/refrigeradores/', 'Refrigerator'],
            ['lavado-y-secado/lavadoras/', 'WashingMachine'],
            ['lavado-y-secado/secadoras/', 'WashingMachine'],
            ['pequenos-electrodomesticos/microondas-y-hornos/', 'Oven'],
            ['pequenos-electrodomesticos/aspiradoras/', 'VacuumCleaner'],
            ['discos-duros/discos-duros-externos/', 'ExternalStorageDrive'],
            # ['tabletas-digitalizadoras/teclados-pc/', 'Keyboard'],
            ['mouse-kit/mouse/', 'Mouse'],
            ['pc-escritorio/all-in-one/', 'AllInOne'],
            ['pc-escritorio/monitores/', 'Monitor'],
        ]
