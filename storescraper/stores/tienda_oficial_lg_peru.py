from .lg_pe import LgPe


class TiendaOficialLgPeru(LgPe):
    skip_products_without_price = True

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = []

        for product in super(TiendaOficialLgPeru, cls).products_for_url(
            url, category, extra_args
        ):
            product.url += "buy/"
            products.append(product)

        return products
