from .falabella_peru import FalabellaPeru


class SodimacPeru(FalabellaPeru):
    store_and_subdomain = "sodimac"
    seller = "SODIMAC"

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        if extra_args is None:
            extra_args = {}

        extra_args.update({"remove_words_blacklist": [","]})

        products = super(SodimacPeru, cls).products_for_url(
            url, category=category, extra_args=extra_args
        )
        for product in products:
            # Falabella base scraper will return the product as unavailable
            # because it has the "SODIMAC" seller blacklisted
            product.stock = -1
            product.seller = None
        return products
