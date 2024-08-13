import json
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    TELEVISION,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Exito(Store):
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
        results_per_page = 16
        while True:
            if page > 20:
                raise Exception("Page overflow")
            print(page)

            payload = {
                "first": results_per_page,
                "after": str(results_per_page * page),
                "sort": "score_desc",
                "term": "lg",
                "selectedFacets": [
                    {"key": "brand", "value": "LG"},
                    {"key": "channel", "value": '{"salesChannel":"1","regionId":""}'},
                    {"key": "vendido-por", "value": "exito"},
                ],
            }

            response = session.get(
                "https://www.exito.com/api/graphql?operationName=QuerySearch&variables={}".format(
                    urllib.parse.quote(json.dumps(payload))
                )
            )
            response_data = response.json()
            hits = response_data["data"]["search"]["products"]["edges"]
            if not hits:
                break

            for hit in hits:
                product_url = "https://www.exito.com/{}/p".format(hit["node"]["slug"])
                product_urls.append(product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        soup = BeautifulSoup(res.text, "lxml")
        product_json = json.loads(soup.find("script", {"id": "__NEXT_DATA__"}).text)[
            "props"
        ]["pageProps"]["data"]["product"]
        name = product_json["name"]
        key = product_json["id"]
        picture_urls = [x["url"] for x in product_json["image"]]
        sku = product_json["sku"]
        price = Decimal(product_json["offers"]["lowPrice"])

        if not price:
            return []

        offer = product_json["offers"]["offers"][0]
        if offer["availability"] == "https://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            "COP",
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
