from .ripley import Ripley


class MercadoRipley(Ripley):
    @classmethod
    def filter_url(cls, url):
        return '-mpm' in url
