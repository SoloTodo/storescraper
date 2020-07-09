from .ripley_chile_base_cf import RipleyChileBaseCf


class MercadoRipleyCf(RipleyChileBaseCf):
    @classmethod
    def filter_url(cls, url):
        return '-mpm' in url
