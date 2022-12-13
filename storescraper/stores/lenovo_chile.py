from .lenovo import Lenovo


class LenovoChile(Lenovo):
    region_extension = '/cl/es'
    currency = 'CLP'
