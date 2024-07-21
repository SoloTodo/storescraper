import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class FantasiaElectronica(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []
        session = session_with_proxy(extra_args)
        session.headers["accept"] = "application/json, text/javascript, */*; q=0.01"
        product_urls = []
        url = "https://fantasiaelectronica.com.co/19_lg"
        res = session.get(url)
        products_data = res.json()

        for product in products_data["products"]:
            product_url = product["canonical_url"]
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        json_data = json.loads(
            soup.find("div", {"id": "product-details"})["data-product"]
        )

        key = str(json_data["id_product"])
        name = json_data["name"]
        description = html_to_markdown(json_data["description"])
        stock = json_data["quantity"]
        price = Decimal(json_data["price"])

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
            sku=key,
            description=description,
        )
        return [p]
