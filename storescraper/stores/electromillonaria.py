import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Electromillonaria(Store):
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
            if page > 10:
                raise Exception("Page overflow")
            url = "https://electromillonaria.co/product-brand/lg/page/{}/".format(page)
            print(url)
            res = session.get(url)
            if res.status_code == 404:
                break
            soup = BeautifulSoup(res.text, "html.parser")

            for product in soup.find("div", "main-products").findAll(
                "section", "product"
            ):
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
        qty_input = soup.find("input", "input-text qty text")
        stock = int(qty_input["max"])

        product_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )["@graph"][1]
        name = product_data["name"]
        sku = str(product_data["sku"])
        price = Decimal(product_data["offers"][0]["price"])
        description = product_data["description"]

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
            description=description,
        )
        return [p]
