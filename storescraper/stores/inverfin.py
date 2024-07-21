import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Inverfin(Store):
    base_url = "https://www.lg.com"
    country_code = "cl"

    @classmethod
    def categories(cls):
        return [
            "Television",
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        if category != "Television":
            return []

        page = 1

        while True:
            url = "https://inverfin.com.py/search?type=product&q=LG&page=" + str(page)
            print(url)

            if page >= 15:
                raise Exception("Page overflow " + url)

            soup = BeautifulSoup(session.get(url).text, "lxml")
            product_containers = soup.find("ul", "product-grid")

            if not product_containers:
                if page == 1:
                    raise Exception("Empty category: " + url)
                break

            for product in product_containers.findAll("li", "grid__item"):
                product_link = product.find("a")

                if "LG" not in product_link.text.upper():
                    continue

                product_url = "https://inverfin.com.py{}".format(
                    product_link["href"].split("?")[0]
                )
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, "lxml")

        product_tag = soup.find("script", {"data-product-json": True})
        product_json = json.loads(product_tag.text)
        products = []
        base_name = product_json["title"]
        picture_urls = [
            "https:" + x["sizes"]["original"] for x in product_json["images"]
        ]
        for variant in product_json["variants"]:
            name = "{} ({})".format(base_name, variant["title"])
            sku = variant["sku"]
            key = str(variant["id"])

            if "LG" not in name.upper():
                stock = 0
            elif variant["available"]:
                stock = -1
            else:
                stock = 0

            price = Decimal(variant["price"] / 100)

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
                "PYG",
                sku=sku,
                picture_urls=picture_urls,
            )
            products.append(p)
        return products
