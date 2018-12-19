from .lg_chile import LgChile


class LgPanama(LgChile):
    country_code = 'pa'

    @classmethod
    def _category_paths(cls):
        return [
            ('CT20188038', 'CT20188038', 'Television', True),
            # ('CT20188038', 'CT20188038', 'Television', False),
            ('CT20188052', 'CT20188052', 'StereoSystem', True),
            # ('CT20188052', 'CT20188052', 'StereoSystem', False),
            ('CT20188049', 'CT20188050', 'StereoSystem', True),
            # ('CT20188049', 'CT20188050', 'StereoSystem', False),
            ('CT30015340', 'CT30015340', 'StereoSystem', True),
            # ('CT30015340', 'CT30015340', 'StereoSystem', False),
            ('CT20188055', 'CT20188057', 'OpticalDiskPlayer', True),
            # ('CT20188055', 'CT20188057', 'OpticalDiskPlayer', False),
            ('CT20188055', 'CT20188056', 'OpticalDiskPlayer', True),
            # ('CT20188055', 'CT20188056', 'OpticalDiskPlayer', False),
            ('CT20188025', 'CT20188025', 'Projector', True),
            ('CT20188032', 'CT20188032', 'Cell', True),
            # ('CT20188032', 'CT20188032', 'Cell', False),
            ('CT30006720', 'CT30006720', 'Headphones', True),
            # ('CT30006720', 'CT30006720', 'Headphones', False),
            ('CT20188021', 'CT20188021', 'Refrigerator', True),
            # ('CT20188021', 'CT20188021', 'Refrigerator', False),
            ('CT20188014', 'CT20188014', 'WashingMachine', True),
            # ('CT20188014', 'CT20188014', 'WashingMachine', False),
            ('CT32015142', 'CT32015142', 'WashingMachine', True),  # Styler
            ('CT20188013', 'CT20188013', 'VacuumCleaner', True),  # Aspiradoras
            # ('CT20188013', 'CT20188013', 'VacuumCleaner', False),
            ('CT30015260', 'CT30015260', 'Oven', True),  # Hornos Y Estufas
            # ('CT30015260', 'CT30015260', 'Oven', False),
            ('CT20188009', 'CT20188009', 'Oven', True),  # Microondas
            # ('CT20188009', 'CT20188009', 'Oven', False),
            ('CT30015420', 'CT30015420', 'DishWasher', True),  # Lavaplatos
            # Aire Acondicionado Split Inverter
            ('CT30014140', 'CT30014241', 'AirConditioner', True),
            # ('CT30014140', 'CT30014241', 'AirConditioner', False),
            # Aire Acondicionado Split Convencional
            # ('CT30014140', 'CT30014242', 'AirConditioner', True),
            # Aire Acondicionado de Ventana
            # ('CT30014140', 'CT30014240', 'AirConditioner', True),

        ]
