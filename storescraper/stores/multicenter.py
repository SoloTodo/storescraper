import base64
import urllib
from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, vtex_preflight


class Multicenter(Store):
    base_url = "https://www.multicenter.com.bo"

    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        offset = 0
        while True:
            if offset >= 120:
                raise Exception("Page overflow")

            variables = {
                "from": offset,
                "to": offset + 40,
                "fullText": "lg",
            }

            payload = {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": extra_args["sha256Hash"],
                },
                "variables": base64.b64encode(
                    json.dumps(variables).encode("utf-8")
                ).decode("utf-8"),
            }

            endpoint = (
                "https://www.multicenter.com.bo/_v/segment/graphql/"
                "v1?extensions={}".format(urllib.parse.quote(json.dumps(payload)))
            )
            response = session.get(endpoint).json()

            product_entries = response["data"]["productSearch"]["products"]

            if not product_entries:
                break

            for product_entry in product_entries:
                product_url = "https://www.multicenter.com.bo/{}/p".format(
                    product_entry["linkText"]
                )
                product_urls.append(product_url)

            offset += 40
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        json_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )

        key = json_data["mpn"]
        name = json_data["name"]
        sku = json_data["sku"]
        price = Decimal(str(json_data["offers"]["offers"][0]["price"]))

        if soup.find("div", "vtex-add-to-cart-button-0-x-buttonDataContainer"):
            stock = -1
        else:
            stock = 0

        picture_container = soup.findAll("div", "swiper-container")[-1]
        picture_urls = []
        for i in picture_container.findAll("img"):
            picture_urls.append(i["src"])

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
            "BOB",
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]

    @classmethod
    def preflight(cls, extra_args=None):
        return vtex_preflight(extra_args, "https://www.multicenter.com.bo/electrohogar")
