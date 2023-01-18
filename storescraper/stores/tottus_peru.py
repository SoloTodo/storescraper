from .falabella_peru import FalabellaPeru


class TottusPeru(FalabellaPeru):
    seller = 'TOTTUS'
    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super(TottusPeru, cls).products_for_url(
            url, category=category, extra_args=extra_args)
        for product in products:
            product.seller = None
        return products
