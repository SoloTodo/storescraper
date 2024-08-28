import json
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Tauret(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []
        session = session_with_proxy(extra_args)
        product_urls = []
        url = "https://tauretcomputadores.com/search_product?product_search=LG"
        print(url)
        res = session.get(url)
        soup = BeautifulSoup(res.text, "lxml")
        product_container = soup.find("search-products")
        products_data = json.loads(product_container["productos"])

        for product in products_data:
            product_brand_id = product["brands_id"]
            # LG is 34
            if product_brand_id != 34:
                continue
            product_url = "https://tauretcomputadores.com/product/" + product["slug"]
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        product_tag = soup.find("button-add-cart")

        if not product_tag:
            return []

        product_data = json.loads(product_tag[":product"])
        name = product_data["title"]
        key = str(product_data["id"])
        stock = -1 if product_data["quantity"] else 0
        price = Decimal(product_data["price"])
        description = html_to_markdown(product_data["description"])
        picture_urls = [
            "https://tauretcomputadores.com/images/products/"
            + urllib.parse.quote(x["link_imagen"])
            for x in product_data["images"]
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
            description=description,
            picture_urls=picture_urls,
        )
        return [p]
