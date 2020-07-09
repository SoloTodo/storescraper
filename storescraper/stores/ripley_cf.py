from .ripley_chile_base_cf import RipleyChileBaseCf


class RipleyCf(RipleyChileBaseCf):
    @classmethod
    def filter_url(cls, url):
        return '-mpm' not in url
