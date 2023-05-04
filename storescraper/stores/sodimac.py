from .falabella import Falabella


class Sodimac(Falabella):
    store_and_subdomain = 'sodimac'
    seller = [('SODIMAC', None)]
    seller_blacklist = []

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super().products_for_url(url, category=category,
                                            extra_args=extra_args)

        for product in products:
            product.url = url
            product.discovery_url = url
            product.seller = None

        return products
