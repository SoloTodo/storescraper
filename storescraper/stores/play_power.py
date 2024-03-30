import json
import re
from decimal import Decimal
import logging

import pyjson5
from bs4 import BeautifulSoup

from storescraper.categories import MONITOR
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class PlayPower(StoreWithUrlExtensions):
    url_extensions = [
        ["all", MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://playpower.cl/collections/{}?page={}".format(
                url_extension, page
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html.parser")
            product_containers = soup.findAll("li", "grid__item")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_path = container.find("a")["href"]
                product_urls.append("https://playpower.cl" + product_path)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        products = []
        name_tag = soup.find("h3", {"data-product-type": "title"})

        if name_tag:
            name_tag = soup.find("h3", {"data-product-type": "title"})
            page_id = name_tag["data-product-id"]

            search_string = (
                r'window.__pageflyProducts\["'
                + re.escape(page_id)
                + r'"] = ([\s\S]+?);'
            )
            match = re.search(search_string, response.text)
            product_data = pyjson5.decode(match.groups()[0])

            base_name = product_data["title"]
            picture_urls = ["https:" + x["src"] for x in product_data["media"]]
            for variant in product_data["variants"]:
                name = "{} ({})".format(base_name, variant["title"])
                key = str(variant["id"])
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
                    "CLP",
                    picture_urls=picture_urls,
                )
                products.append(p)
        else:
            variants_tag = soup.find("variant-radios")

            if not variants_tag:
                return []

            base_name = soup.find("h1").text.strip()
            variants_data = json.loads(variants_tag.find("script").text)
            for variant in variants_data:
                name = "{} ({})".format(base_name, variant["title"])
                key = str(variant["id"])
                stock = -1 if variant["available"] else 0
                price = Decimal(variant["price"] // 100)
                if variant["featured_image"]:
                    picture_urls = ["https:" + variant["featured_image"]["src"]]
                else:
                    picture_urls = None

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
                    "CLP",
                    picture_urls=picture_urls,
                )
                products.append(p)
        return products
