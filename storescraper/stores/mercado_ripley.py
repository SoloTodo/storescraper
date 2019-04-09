from .ripley_chile_base import RipleyChileBase


class MercadoRipley(RipleyChileBase):
    @classmethod
    def filter_url(cls, url):
        return '-mpm' in url
