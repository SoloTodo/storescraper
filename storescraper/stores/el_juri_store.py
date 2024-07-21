import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class ElJuriStore(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow")

            url_webpage = "https://eljuri.store/brand/19-lg?page={}".format(page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("article", "product-miniature")

            if not product_containers:
                if page == 1:
                    logging.warning("Empty category")
                break
            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        json_tags = soup.findAll("script", {"type": "application/ld+json"})

        for tag in json_tags:
            entry = json.loads(tag.text)
            if entry["@type"] == "Product":
                product_data = entry
                break
        else:
            return []

        name = product_data["name"]
        sku = str(product_data["mpn"])
        description = product_data["description"]
        price = Decimal(product_data["offers"]["price"])

        stock_tag = soup.find("div", "product-quantities").find("span")
        if "data-stock" in stock_tag.attrs:
            stock = int(stock_tag["data-stock"])
        else:
            stock = 0
        picture_urls = [product_data["image"]]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            "USD",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
