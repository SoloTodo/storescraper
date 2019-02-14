from .lg_chile import LgChile


class LgPanama(LgChile):
    country_code = 'pa'

    @classmethod
    def _category_paths(cls):
        return [
            ('CT20188038', 'CT20188038', 'Television', True),
            # ('CT20188052', 'CT20188052', 'StereoSystem', True),
            ('CT20188049', 'CT32016442', 'StereoSystem', True),  # OneBody
            # Minicomponentes
            ('CT20188049', 'CT20188050', 'StereoSystem', True),
            # Barra de sonido
            # ('CT20188049', 'CT32016444', 'StereoSystem', True),
            # Parlantes Bluetooth
            ('CT20188049', 'CT32016443', 'StereoSystem', True),
            ('CT20188055', 'CT20188057', 'OpticalDiskPlayer', True),
            ('CT20188055', 'CT20188056', 'OpticalDiskPlayer', True),
            ('CT20188025', 'CT20188025', 'Projector', True),
            ('CT20188032', 'CT20188032', 'Cell', True),
            ('CT30006720', 'CT30006720', 'Headphones', True),
            ('CT20188021', 'CT20188021', 'Refrigerator', True),
            ('CT20188014', 'CT20188014', 'WashingMachine', True),
            ('CT32015142', 'CT32015142', 'WashingMachine', True),  # Styler
            ('CT20188013', 'CT20188013', 'VacuumCleaner', True),  # Aspiradoras
            ('CT30015260', 'CT30015260', 'Oven', True),  # Hornos Y Estufas
            ('CT20188009', 'CT20188009', 'Oven', True),  # Microondas
            ('CT30015420', 'CT30015420', 'DishWasher', True),  # Lavaplatos
            # Aire Acondicionado Split Inverter
            ('CT30014140', 'CT30014241', 'AirConditioner', True),
            # Aire Acondicionado Split Convencional
            # ('CT30014140', 'CT30014242', 'AirConditioner', True),
            # Aire Acondicionado de Ventana
            # ('CT30014140', 'CT30014240', 'AirConditioner', True),

        ]
