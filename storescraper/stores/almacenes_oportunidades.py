import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class AlmacenesOportunidades(Store):
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

            url = "https://www.oportunidades.com.co/lg?PageNumber={}".format(page)
            res = session.get(url)
            soup = BeautifulSoup(res.text, "lxml")
            products_container = soup.find("div", "n1colunas")

            if not products_container:
                if page == 1:
                    raise Exception("Empty page: " + url)
                break

            for product in products_container.findAll("li", "last"):
                product_url = product.find("a")["href"]
                print(product_url)
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        product_match = re.search(r"var skuJson_0 = (.+)}", res.text).groups()[0]
        product_data = json.loads(product_match + "}")

        products = []
        for variant in product_data["skus"]:
            name = variant["skuname"]
            key = str(variant["sku"])
            stock = -1 if variant["availablequantity"] else 0
            price = Decimal(variant["bestPrice"] // 100)
            picture_urls = [variant["image"]]
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
            products.append(p)

        return products
