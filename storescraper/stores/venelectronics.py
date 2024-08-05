import json
from decimal import Decimal
from bs4 import BeautifulSoup
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import TELEVISION


class Venelectronics(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1

        while True:
            if page > 30:
                raise Exception("Page overflow")

            url = "https://venelectronics.com/search?page={}&q=LG".format(page)
            print(url)
            soup = BeautifulSoup(session.get(url).text, "lxml")
            products = soup.find("main", "main-content").findAll("a", "product-card")

            if not products:
                if page == 1:
                    raise Exception("Empty url {}".format(url))
                else:
                    break

            for product in products:
                product_url = (
                    "https://venelectronics.com" + product["href"].split("?")[0]
                )
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        json_tag = soup.find("script", {"id": "ProductJson-product-template"})
        json_data = json.loads(json_tag.text)

        picture_urls = ["https:" + x.split("?")[0] for x in json_data["images"]]
        description = html_to_markdown(json_data["description"])

        products = []
        for variant in json_data["variants"]:
            price = Decimal(variant["price"]) / Decimal(100)

            if price == 0:
                continue

            name = variant["name"]
            sku = variant["sku"] or None
            key = str(variant["id"])
            stock = -1 if variant["available"] else 0

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
                "USD",
                sku=sku,
                part_number=sku,
                picture_urls=picture_urls,
                description=description,
            )
            products.append(p)

        return products
