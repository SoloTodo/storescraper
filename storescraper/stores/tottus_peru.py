from .falabella_peru import FalabellaPeru


class TottusPeru(FalabellaPeru):
    store_and_subdomain = 'tottus'
    seller = 'TOTTUS'

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super(TottusPeru, cls).products_for_url(
            url, category=category, extra_args=extra_args)
        for product in products:
            # Falabella base scraper will return the product as unavailable
            # because it has the "TOTTUS" seller blacklisted
            product.stock = -1
            product.seller = None
        return products
