from storescraper import banner_sections as bs
from .falabella import Falabella


class Sodimac(Falabella):
    store_and_subdomain = "sodimac"
    seller = [{"id": "SODIMAC", "section_prefix": None, "include_in_fast_mode": True}]
    seller_blacklist = []
    banners_base_url = "https://sodimac.falabella.com/sodimac-cl/{}"
    banners_sections_data = [
        [bs.HOME, "Home", bs.SUBSECTION_TYPE_HOME, ""],
    ]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super().products_for_url(
            url, category=category, extra_args=extra_args
        )

        for product in products:
            product.url = url
            product.discovery_url = url
            product.seller = None

        return products
