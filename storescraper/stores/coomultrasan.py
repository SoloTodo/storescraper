import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Coomultrasan(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []
        session = session_with_proxy(extra_args)
        product_urls = []
        # I have no idea if this store has pagination
        url = "https://www.coomultrasan.com.co/ccstoreui/v1/search?No=0&Nrpp=40&Ntt=LG"
        print(url)
        res = session.get(url)
        json_data = res.json()
        product_containers = json_data["resultsList"]["records"]

        for product in product_containers:
            product_url = (
                "https://www.coomultrasan.com.co"
                + product["records"][0]["attributes"]["product.route"][0]
            )
            product_urls.append(product_url)

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
        key = url.split("/")[-1]
        name = product_data["name"]
        price = Decimal(product_data["offers"][0]["price"])
        description = product_data["description"]
        if product_data["offers"][0]["availability"] == "http://schema.org/InStock":
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
            sku=key,
            description=description,
        )
        return [p]
