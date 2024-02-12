from decimal import Decimal

from storescraper.categories import (
    TELEVISION,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Alkosto(Store):
    algolia_endpoint = (
        "https://qx5ips1b1q-dsn.algolia.net/1/indexes/*/queries?x-algolia-api-key="
        "27485cf29f11a3b2053e9941e49914cf&x-algolia-application-id=QX5IPS1B1Q"
    )
    index_name = "alkostoIndexAlgoliaPRD"
    base_url = "https://www.alkosto.com"

    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []
        page = 0
        while True:
            if page > 10:
                raise Exception("page overflow")
            print(page)

            payload = {
                "requests": [
                    {
                        "indexName": cls.index_name,
                        "params": "filters=allcategories_string_mv:marcas AND allcategories_string_mv:lg&page={}".format(
                            page
                        ),
                    }
                ]
            }

            response = session.post(
                cls.algolia_endpoint,
                json=payload,
            )
            response_data = response.json()
            hits = response_data["results"][0]["hits"]
            if not hits:
                break

            for hit in hits:
                product_url = cls.base_url + hit["url_es_string"]
                product_urls.append(product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_id = url.split("/")[-1]

        payload = {
            "requests": [
                {
                    "indexName": cls.index_name,
                    "params": "query={}".format(page_id),
                }
            ]
        }

        response = session.post(
            cls.algolia_endpoint,
            json=payload,
        )
        response_data = response.json()
        hit = response_data["results"][0]["hits"][0]
        assert hit["code_string"] == page_id
        name = hit["name_text_es"]
        stock = hit["stocklevel_int"]
        price = Decimal(hit["lowestprice_double"])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            page_id,
            stock,
            price,
            price,
            "COP",
            sku=page_id,
        )
        return [p]
