from .linio import Linio
from ..categories import GAMING_CHAIR


class LinioChile(Linio):
    base_domain = 'https://www.linio.cl'
    currency = 'CLP'

    @classmethod
    def _category_paths(cls):
        return [
            ['computacion/pc-portatil', 'Notebook'],
            ['zona-gamer/notebook-gamer', 'Notebook'],
            ['zona-gamer/monitores-gamers', 'Monitor'],
            ['celulares-y-smartphones/liberados', 'Cell'],
            ['tv-y-video/televisores/', 'Television'],
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
            ['mouse-kit/mouse/', 'Mouse'],
            ['pc-escritorio/all-in-one/', 'AllInOne'],
            ['pc-escritorio/monitores/', 'Monitor'],
            ['componentes-de-computadoras/gabinetes/', 'ComputerCase'],
            ['componentes-de-computadoras/procesadores/', 'Processor'],
            ['componentes-de-computadoras/placas-madre/', 'Motherboard'],
            ['componentes-de-computadoras/memoria-ram/', 'Ram'],
            ['componentes-de-computadoras/tarjetas-de-video/', 'VideoCard'],
            ['componentes-de-computadoras/memoria-interna/',
             'SolidStateDrive'],
            ['accesorios-gamers/sillas-gamer', GAMING_CHAIR]
        ]
