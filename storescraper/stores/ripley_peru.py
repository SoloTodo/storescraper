import json
import re

from decimal import Decimal

import validators
from bs4 import BeautifulSoup
from ..categories import TELEVISION
from ..product import Product
from ..store import Store
from curl_cffi import requests


class RipleyPeru(Store):
    # Only returns LG products
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        product_urls = []
        session = requests.Session(impersonate="chrome120")

        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow")

            url = "https://simple.ripley.com.pe/tecnologia/marcas/ver-todo-lg?page={}".format(
                page
            )
            print(url)
            response = session.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            product_containers = soup.findAll("div", "catalog-product-item")
            if not product_containers:
                break
            for container in product_containers:
                product_url = (
                    "https://simple.ripley.com.pe" + container.find("a")["href"]
                )
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = requests.Session(impersonate="chrome120")
        response = session.get(url)
        match = re.search(r"window.__PRELOADED_STATE__ = (.+);", response.text)
        raw_json = match.groups()[0]
        json_data = json.loads(raw_json)
        product_entry = json_data["product"]["product"]

        name = product_entry["name"]
        sku_entry = product_entry["SKUs"][0]
        sku = sku_entry["partNumber"]

        seller_id = product_entry["sellerOp"]["seller_id"]
        if seller_id == 1:
            seller = None
        else:
            seller = product_entry["sellerOp"]["shop_name"]

        if seller:
            stock = 0
        elif product_entry["buyable"]:
            stock = -1
        else:
            stock = 0

        normal_price = Decimal(sku_entry["prices"]["offerPrice"]).quantize(
            Decimal("0.01")
        )

        if "cardPrice" in sku_entry["prices"]:
            offer_price = Decimal(sku_entry["prices"]["cardPrice"]).quantize(
                Decimal("0.01")
            )
        else:
            offer_price = normal_price

        if offer_price > normal_price:
            offer_price = normal_price

        picture_urls = []
        for x in product_entry["images"]:
            if x.startswith("http"):
                picture_url = x
            else:
                picture_url = "https:" + x

            if validators.url(picture_url):
                picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            product_entry["url"],
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            "PEN",
            sku=sku,
            picture_urls=picture_urls,
            seller=seller,
        )

        return [p]
