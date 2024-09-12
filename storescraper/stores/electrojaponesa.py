import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Electrojaponesa(Store):
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

            url = f"https://www.electrojaponesa.com/lg?page={page}"
            print(url)
            res = session.get(url)
            soup = BeautifulSoup(res.text, "lxml")
            product_containers = soup.findAll(
                "section", "vtex-product-summary-2-x-container"
            )

            if not product_containers:
                break

            for product in product_containers:
                product_url = product.find("a")["href"]
                product_urls.append(f"https://www.electrojaponesa.com{product_url}")

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)

        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        product_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )
        offers = product_data["offers"]["offers"]

        assert len(offers) == 1

        offer = offers[0]
        name = product_data["name"]
        key = str(offer["sku"])
        stock = -1 if offer["availability"] == "http://schema.org/InStock" else 0
        price = Decimal(offer["price"])
        picture_urls = [
            img["src"]
            for img in soup.findAll("img", "vtex-store-components-3-x-productImageTag")
        ]

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
            picture_urls=picture_urls,
        )

        return [p]
