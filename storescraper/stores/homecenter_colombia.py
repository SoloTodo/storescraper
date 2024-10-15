import json
import math
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13


class HomecenterColombia(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # ONLY CONSIDERS LG SKUs

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        discovered_urls = []
        page = 1

        while True:
            if page >= 50:
                raise Exception("Page overflow")

            endpoint = (
                "https://www.homecenter.com.co/s/search/v1/soco?q=LG&currentpage={}&"
                "f.product.brandName=lg"
            ).format(page)
            print(endpoint)
            res = session.get(endpoint).json()

            if not res["data"]["results"]:
                break

            for product_entry in res["data"]["results"]:
                product_url = (
                    "https://www.homecenter.com.co/homecenter-co/product/"
                ) + product_entry["productId"]
                discovered_urls.append(product_url)

            # The page thows a 500 error on page overflow so break at the end of the last page
            if page == math.ceil(
                res["data"]["pagination"]["count"]
                / res["data"]["pagination"]["perPage"]
            ):
                break

            page += 1

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        # lxml parser fails for this scraper
        soup = BeautifulSoup(res.text, "html.parser")
        next_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        json_data = json.loads(next_tag.text)
        product_data = json_data["props"]["pageProps"]["productProps"]["result"]
        products = []

        for variant in product_data["variants"]:
            name = "{} {}".format(product_data["brandName"], variant["name"])
            key = variant["id"]
            if check_ean13(variant["upc"]):
                ean = variant["upc"]
            else:
                ean = None
            stock = -1
            description = variant["description"]

            min_price = Decimal("Inf")

            assert len(variant["price"])

            for price_entry in variant["price"]:
                price = Decimal(price_entry["priceWithoutFormatting"]).quantize(
                    Decimal("0.01")
                )
                if price < min_price:
                    min_price = price

            picture_urls = [image["url"] for image in variant["images"]]

            p = Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                min_price,
                min_price,
                "COP",
                sku=key,
                picture_urls=picture_urls,
                description=description,
                ean=ean,
            )

            products.append(p)
        return products
