from .linio import Linio


class LinioMexico(Linio):
    base_domain = 'https://www.linio.com.mx'
    currency = 'MXN'

    @classmethod
    def _category_paths(cls):
        return [
            ['celulares-y-tablets/celulares-y-smartphones', 'Cell'],
            ['tv-y-video/pantallas', 'Television'],
            ['computacion/pc-portatil', 'Notebook'],
            ['zona-gamer/laptop-gamer', 'Notebook'],
            ['pc-escritorio/monitores', 'Monitor'],
            ['discos-duros/discos-duros-internos', 'StorageDrive'],
            ['discos-duros/disco-duro-ssd', 'SolidStateDrive'],
            ['componentes-de-computadoras/gabinete-de-pc', 'ComputerCase'],
            ['componentes-de-computadoras/procesadores', 'Processor'],
            ['componentes-de-computadoras/tarjetas-de-video', 'VideoCard'],
            ['componentes-de-computadoras/tarjetas-madre', 'Motherboard'],
            ['componentes-de-computadoras/memoria-ram', 'Ram'],
            ['xbox-videojuegos/consolas-xbox', 'VideoGameConsole'],
            ['playstation-videojuegos/consolas-playstation',
             'VideoGameConsole'],
            ['nintendo-videojuegos/consolas-nintendo', 'VideoGameConsole'],
        ]
