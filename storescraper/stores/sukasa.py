import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import TELEVISION


class Sukasa(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        session.headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.3"
        )

        product_urls = []
        page = 1
        while True:
            endpoint = "https://api.comohogar.com//catalog-api/products-es/all-by-category-tree?page={}&pageSize=10&active=true&brandId=60966430-ee8d-11ed-b56d-005056010420".format(
                page
            )
            print(endpoint)
            response = session.get(endpoint)
            products_data = response.json()["entities"]

            if not products_data:
                break

            for product in products_data[0]["products"]:
                product_url = "https://www.sukasa.com/productos/{}?id={}".format(
                    product["slug"], product["id"]
                )
                if product_url not in product_urls:
                    product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.3"
        )

        product_id = url.split("?id=")[1]
        endpoint = (
            "https://api.comohogar.com//catalog-api/products/portal/" + product_id
        )
        response = session.get(endpoint)
        product_data = response.json()
        name = product_data["name"]
        sku = product_data["cmInternalCode"]
        stock = product_data["cmStock"] or 0

        for store in product_data["storeList"]:
            stock += store["quantity"]

        offer_price = Decimal(str(product_data["cmItmPvpAfIva"])).quantize(
            Decimal("0.01")
        )
        normal_price = Decimal(str(product_data["cmItmPvpNafIva"])).quantize(
            Decimal("0.01")
        )
        picture_urls = [x["resourceUrl"] for x in product_data["resources"]]
        description = html_to_markdown(product_data["longDescription"])

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
            "USD",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
