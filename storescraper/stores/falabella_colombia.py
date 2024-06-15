from storescraper.categories import TELEVISION
from storescraper.store import Store
from storescraper.utils import session_with_proxy, CF_REQUEST_HEADERS


class FalabellaColombia(Store):
    store_and_subdomain = None
    seller = "FALABELLA"

    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # ONLY CONSIDERS LG SKUs

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = CF_REQUEST_HEADERS["User-Agent"]

        discovered_urls = []
        page = 1

        while True:
            if page >= 50:
                raise Exception("Page overflow")

            endpoint = (
                "https://www.falabella.com.co/s/browse/v1/search/co?f.product.brandName=lg&Ntt=lg&page={}&"
                "pid=bbea9a06-99b1-44de-bc6e-d314bca4fad3&f.derived.variant.sellerId=FALABELLA".format(
                    page
                )
            )

            res = session.get(endpoint).json()

            if not res["data"]["results"]:
                break

            for product_entry in res["data"]["results"]:
                discovered_urls.append(product_entry["url"])

            page += 1

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        from .falabella import Falabella

        extra_args = extra_args or {}
        extra_args["use_cf"] = False

        products = Falabella.products_for_url(
            url, category=category, extra_args=extra_args
        )

        for product in products:
            product.store = cls.__name__
            product.currency = "COP"
            product.url = url
            product.discovery_url = url

        return products
