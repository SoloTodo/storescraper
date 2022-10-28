from decimal import Decimal
from storescraper.stores import SamsungChile


class SamsungShop(SamsungChile):
    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = []

        for product in super(SamsungShop, cls).products_for_url(
                url, category=category, extra_args=extra_args):
            if product.normal_price > Decimal(0):
                products.append(product)

        return products
