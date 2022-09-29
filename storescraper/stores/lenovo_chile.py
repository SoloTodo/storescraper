from .lenovo import Lenovo


class LenovoChile(Lenovo):
    region_extension = '/cl/es'
    currency = 'CLP'
    extension = 'CL%7CB2C%7CCLWEB%7CES_CL'
