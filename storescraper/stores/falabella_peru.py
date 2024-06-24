from storescraper.categories import TELEVISION
from storescraper.store import Store
from storescraper.utils import session_with_proxy, CF_REQUEST_HEADERS


class FalabellaPeru(Store):
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
                "https://www.falabella.com.pe/s/browse/v1/brand/pe"
                "?page={}&pid=799c102f-9b4c-44be-a421-23e366a63b82"
                "&brandName=LG&zones=IBIS_51%2CPPE3342%2CPPE3361%2CPPE1112%2CPPE3384%2C912_LIMA_2%2CPPE1280%2C150000"
                "%2CPPE4%2C912_LIMA_1%2CPPE1279%2C150101%2CPPE344%2CPPE3059%2CPPE2492%2CIMP_2%2CPPE3331%2CPPE3357"
                "%2CPPE1091%2CPERF_TEST%2CPPE1653%2CPPE2486%2COLVAA_81%2CPPE2815%2CIMP_1%2CPPE3164%2CPPE2918"
                "%2CURBANO_83%2CPPE2429%2CPPE3152%2CPPE3479%2CPPE3483%2CPPE3394%2CLIMA_URB1_DIRECTO%2CPPE2511"
                "%2CIBIS_19%2CPPE1382%2CIBIS_3PL_83%2CPPE3248".format(page)
            )

            if cls.store_and_subdomain:
                endpoint += "&subdomain={}&store={}".format(
                    cls.store_and_subdomain, cls.store_and_subdomain
                )

            if cls.seller:
                endpoint += "&f.derived.variant.sellerId={}".format(cls.seller)

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
            product.currency = "PEN"
            product.url = url
            product.discovery_url = url

        return products
