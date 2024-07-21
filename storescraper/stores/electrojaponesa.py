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
            url = (
                "https://www.electrojaponesa.com/buscapagina?fq=B%3a2000013&PS=12&"
                "sl=dd7e433e-5e08-4153-9a84-f0efc19710d9&cc=3&sm=0&PageNumber={}"
            ).format(page)
            print(url)
            res = session.get(url)
            soup = BeautifulSoup(res.text, "lxml")

            product_containers = soup.findAll("figure", "vitrina")
            if not product_containers:
                break

            for product in product_containers:
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        product_match = re.search(r"var skuJson_0 = (.+)}", response.text).groups()[0]
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
