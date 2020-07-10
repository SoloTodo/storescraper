from .ripley_chile_base_cf import RipleyChileBaseCf
from .ripley import Ripley


class RipleyCf(RipleyChileBaseCf):
    @classmethod
    def filter_url(cls, url):
        return '-mpm' not in url

    @classmethod
    def banners(cls, extra_args=None):
        return Ripley.banners(extra_args)
