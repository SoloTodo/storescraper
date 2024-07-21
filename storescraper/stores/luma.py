import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Luma(Store):
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
            if page >= 15:
                raise Exception("Page overflow")

            url = "https://luma.com.co/collections/lg?page={}".format(page)

            soup = BeautifulSoup(session.get(url).text, "lxml")
            products_container = soup.findAll("div", "engoc-product-item")

            if not products_container:
                if page == 1:
                    raise Exception("Empty site: {}".format(url))
                break

            for product in products_container:
                product_url = "https://luma.com.co" + product.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        product_data = json.loads(
            re.search(r"product: (.+)", res.text).groups()[0][:-1]
        )
        description = html_to_markdown(product_data["description"])
        picture_urls = ["https:" + x for x in product_data["images"]]
        products = []
        for variant in product_data["variants"]:
            name = variant["name"]
            key = str(variant["id"])
            sku = variant["sku"]
            stock = -1 if variant["available"] else 0
            price = Decimal(variant["price"] // 100)
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
                picture_urls=picture_urls,
                description=description,
            )
            products.append(p)

        return products
