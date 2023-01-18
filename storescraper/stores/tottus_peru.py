from .falabella_peru import FalabellaPeru

class TottusPeru(FalabellaPeru):
    seller = 'TOTTUS'
    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super(SodimacPeru, cls).products_for_url(url, category=None, extra_args=None)
        for product in products:
            product.seller = None
        return products
