import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import KEYBOARD, MONITOR, NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Wisdomts(Store):
    @classmethod
    def categories(cls):
        return [KEYBOARD, MONITOR, NOTEBOOK]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["accessories", KEYBOARD],
            ["monitores", MONITOR],
            ["computadores", NOTEBOOK],
        ]
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = "curl"
        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception("Page overflow")

                url_webpage = (
                    "https://wisdomts.cl/tienda/page/{}/?"
                    "yith_wcan=1&product_cat={}".format(page, url_extension)
                )
                print(url_webpage)
                res = session.get(url_webpage)

                if res.status_code == 404:
                    break

                soup = BeautifulSoup(res.text, "lxml")
                product_containers = soup.findAll("ul", "products")[-1]

                for container in product_containers.findAll("li", "product-grid-view"):
                    product_url = container.find("a")["href"]
                    if "2021-dell-gold-partner" in product_url:
                        continue
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = "curl"
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )

        if "@graph" not in json_data:
            return []

        product_data = json_data["@graph"][1]

        if product_data["offers"][0]["availability"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        picture_urls = [product_data["image"]]
        sku = str(product_data["sku"])
        name = product_data["name"]
        description = product_data["description"]
        offer_price = Decimal(product_data["offers"][0]["price"])
        normal_price = (offer_price * Decimal("1.03")).quantize(0)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            "CLP",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
