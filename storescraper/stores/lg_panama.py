from .lg_chile import LgChile


class LgPanama(LgChile):
    country_code = 'pa'

    @classmethod
    def _category_paths(cls):
        return [
            # Todos los Televisores
            ('CT20188038', 'CT20188038', 'Television', True),
            # Descontinuado TELEVISORES
            ('CT20188038', 'CT20188038', 'Television', False),
            # OneBody
            ('CT20188049', 'CT32016442', 'StereoSystem', True),
            # Minicomponentes
            ('CT20188049', 'CT20188050', 'StereoSystem', True),
            # Barra de sonido
            # ('CT20188049', 'CT32016444', 'StereoSystem', True),
            # Parlantes Bluetooth
            ('CT20188049', 'CT32016443', 'StereoSystem', True),
            # Descontinuado EQUIPO DE SONIDO
            ('CT20188049', 'CT20188049', 'StereoSystem', False),
            ('CT20188055', 'CT20188057', 'OpticalDiskPlayer', True),
            ('CT20188055', 'CT20188056', 'OpticalDiskPlayer', True),
            # Descontinuado VIDEO
            ('CT20188055', 'CT20188055', 'OpticalDiskPlayer', False),
            ('CT20188025', 'CT20188025', 'Projector', True),
            ('CT20188032', 'CT20188032', 'Cell', True),
            # Descontinuado TELÉFONOS CELULARES
            ('CT20188032', 'CT20188032', 'Cell', False),
            ('CT30006720', 'CT30006720', 'Headphones', True),
            # Descontinuado ACCESORIOS PARA CELULAR
            ('CT30006720', 'CT30006720', 'Headphones', False),
            ('CT20188021', 'CT20188021', 'Refrigerator', True),
            # Descontinuado REFRIGERADORA
            ('CT20188021', 'CT20188021', 'Refrigerator', False),
            ('CT20188014', 'CT20188014', 'WashingMachine', True),
            # Styler
            ('CT32015142', 'CT32015142', 'WashingMachine', True),
            # Descontinuado LAVADORAS Y SECADORAS
            ('CT20188014', 'CT20188014', 'WashingMachine', False),
            # Aspiradoras
            ('CT20188013', 'CT20188013', 'VacuumCleaner', True),
            # Descontinuado ASPIRADORAS
            ('CT20188013', 'CT20188013', 'VacuumCleaner', False),
            # Hornos Y Estufas
            ('CT30015260', 'CT30015260', 'Oven', True),
            # Descontinuado HORNOS Y ESTUFAS
            ('CT30015260', 'CT30015260', 'Oven', False),
            # Microondas
            ('CT20188009', 'CT20188009', 'Oven', True),
            # Descontinuado MICROONDAS
            ('CT20188009', 'CT20188009', 'Oven', False),
            # Lavaplatos
            ('CT30015420', 'CT30015420', 'DishWasher', True),
            # Aire Acondicionado Split Inverter
            ('CT30014140', 'CT30014241', 'AirConditioner', True),
            # Aire Acondicionado Split Convencional
            # ('CT30014140', 'CT30014242', 'AirConditioner', True),
            # Aire Acondicionado de Ventana
            # ('CT30014140', 'CT30014240', 'AirConditioner', True),
            # Descontinuado AIRE ACONDICIONADO RESIDENCIAL
            ('CT30014140', 'CT30014140', 'AirConditioner', False),
            # Monitores
            ('CT20188028', 'CT20188028', 'Monitor', True),
            # Descontinuado MONITORES
            ('CT20188028', 'CT20188028', 'Monitor', False),
        ]
