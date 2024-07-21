import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    NOTEBOOK,
    MONITOR,
    TABLET,
    CELL,
    HEADPHONES,
    WEARABLE,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class MacOnline(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            MONITOR,
            TABLET,
            CELL,
            HEADPHONES,
            WEARABLE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = "curl"
        discovered_urls = []

        category_paths = [
            ["mac", NOTEBOOK],
            ["ipad", TABLET],
            ["iphone", CELL],
            ["watch", WEARABLE],
            ["musica", HEADPHONES],
        ]

        for e in category_paths:
            category_path, local_category = e

            if category != local_category:
                continue

            category_url = "https://www.maconline.com/t/{}".format(category_path)
            print(category_url)

            soup = BeautifulSoup(session.get(category_url).text, "lxml")

            products_grid = soup.find("div", {"id": "products"})
            if products_grid:
                page = 1
                while True:
                    if page >= 10:
                        raise Exception("Page overflow")
                    url = "{}?page={}".format(category_url, page)
                    print(url)
                    soup = BeautifulSoup(session.get(url).text, "lxml")
                    products_grid = soup.find("div", {"id": "products"})
                    if not products_grid:
                        break
                    for product_cell in products_grid.findAll(
                        "div", "product-list-item"
                    ):
                        product_url = (
                            "https://www.maconline.com" + product_cell.find("a")["href"]
                        )
                        discovered_urls.append(product_url)
                    page += 1
            else:
                subcategories = soup.find("ul", "list-unstyled").findAll("li")
                assert subcategories

                for idx, subcategory in enumerate(subcategories):
                    product_url = "https://www.maconline.com{}".format(
                        subcategory.find("a")["href"].split("?")[0]
                    )
                    discovered_urls.append(product_url)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        products = []
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = "curl"
        response = session.get(url)

        if not response.ok:
            return []

        page_source = response.text

        soup = BeautifulSoup(page_source, "lxml")
        default_picture_url = soup.find("img", {"itemprop": "image"})
        json_data = re.search(r"options: (.*)", page_source)

        if json_data:
            json_data = json.loads(json_data.groups()[0][:-1])
            json_products = cls.__extract_products(json_data)

            for json_product in json_products.values():
                name = json_product["name"]
                part_number = json_product["sku"]
                sku = str(json_product["id"])
                description = html_to_markdown(json_product["technical_details"])
                description += "\n\n" + html_to_markdown(
                    json_product.get("description", "")
                )

                if "INTERNACIONAL" in name.upper():
                    stock = 0
                elif json_product["in_stock"]:
                    stock = sum(json.loads(json_product["stock_locations"]).values())
                else:
                    stock = 0

                price = Decimal(remove_words(json_product["price"]))

                picture_tag = soup.find("li", "tmb-" + sku)
                if picture_tag:
                    picture_urls = [picture_tag.find("a")["href"]]
                elif default_picture_url:
                    picture_urls = [default_picture_url["data-src"]]
                else:
                    picture_urls = None

                products.append(
                    Product(
                        name,
                        cls.__name__,
                        category,
                        url,
                        url,
                        sku,
                        stock,
                        price,
                        price,
                        "CLP",
                        sku=sku,
                        part_number=part_number,
                        description=description,
                        picture_urls=picture_urls,
                    )
                )
        else:
            json_container = soup.find("script", {"type": "application/ld+json"})
            json_data = json.loads(json_container.text)

            name = json_data["name"]
            sku = json_data["sku"]
            price = Decimal(json_data["offers"]["price"])
            description = html_to_markdown(json_data.get("description", ""))
            picture_urls = [x.split("?")[0] for x in json_data["image"]]

            if "INTERNACIONAL" in name.upper():
                stock = 0
            else:
                stock = -1

            products.append(
                Product(
                    name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    sku,
                    stock,
                    price,
                    price,
                    "CLP",
                    sku=sku,
                    description=description,
                    picture_urls=picture_urls,
                )
            )

        return products

    @classmethod
    def __extract_products(cls, prods):
        if not prods:
            return {}

        if "id" in prods:
            return {prods["id"]: prods}

        result = {}
        for value in prods.values():
            result.update(cls.__extract_products(value))

        return result
