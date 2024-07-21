import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, remove_words


class ProMovil(Store):
    @classmethod
    def categories(cls):
        return [
            "Cell",
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ["6-smartphones", "Cell"],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = "https://www.promovil.cl/{}?page={}".format(
                    category_path, page
                )

                if page >= 20:
                    raise Exception("Page overflow: " + category_url)

                print(category_url)

                response = session.get(category_url)

                if response.url != category_url:
                    raise Exception("Empty category: " + category_url)

                soup = BeautifulSoup(response.text, "lxml")

                products_containers = soup.findAll("div", "item-product")

                if not products_containers:
                    if page == 1:
                        raise Exception("Empty category: " + category_url)
                    break

                for product_container in products_containers:
                    product_url = product_container.find("a")["href"]
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, "lxml")

        attribute_ids_container = soup.find("div", "product-variants-item")

        if not attribute_ids_container:
            sku = soup.find("input", {"name": "id_product"})["value"]
            return [cls.get_single_product(url, sku, category, extra_args)]

        product_json = json.loads(
            soup.find("div", {"id": "product-details"})["data-product"]
        )
        product_id = product_json["id"]
        link_rewrite = product_json["link_rewrite"]
        base_url = "https://www.promovil.cl/inicio/{}-{}-{}.html"

        # Get ids, the hard and only way
        attribute_group = attribute_ids_container.find("input")[
            "data-product-attribute"
        ]
        attribute_ids = [i["value"] for i in attribute_ids_container.findAll("input")]

        id_url_base = (
            "https://www.promovil.cl/index.php?"
            "controller=product&"
            "id_product={}&"
            "group%5B{}%5D={}"
        )
        session.headers["Content-Type"] = (
            "application/x-www-form-urlencoded;" " charset=UTF-8"
        )
        session.headers["Accept"] = "application/json, text/javascript," " */*; q=0.01"

        variants_ids = []

        for attribute_id in attribute_ids:
            id_url = id_url_base.format(product_id, attribute_group, attribute_id)
            variants_ids.append(
                json.loads(session.post(id_url, "action=refresh").text)[
                    "id_product_attribute"
                ]
            )

        # Generate single product urls

        products = []
        for variant_id in variants_ids:
            variant_url = base_url.format(product_id, variant_id, link_rewrite)
            sku = "{}-{}".format(product_id, variant_id)
            products.append(
                cls.get_single_product(variant_url, sku, category, extra_args)
            )

        return products

    @classmethod
    def get_single_product(cls, url, sku, category, extra_args):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, "lxml")

        product_json = json.loads(
            soup.find("div", {"id": "product-details"})["data-product"]
        )
        name_ext = ""

        if "attributes" in product_json:
            for key, value in product_json["attributes"].items():
                name_ext = value["name"]
                break

        name = soup.find("h1", {"itemprop": "name"}).text

        if name_ext:
            name += " ({})".format(name_ext)

        price = Decimal(
            remove_words(soup.find("div", "current-price").find("span").text)
        )

        stock_container = soup.find("span", {"id": "product-availability"})

        if any(w in stock_container.text.lower() for w in ["disponible", "últimas"]):
            stock = -1
        else:
            stock = 0

        description = html_to_markdown(str(soup.find("div", "product-desc")))
        description += html_to_markdown(str(soup.find("div", "product-description")))

        images_containers = soup.find("ul", "product-images").findAll("li")
        picture_urls = []

        for image in images_containers:
            picture_url = image.find("img")["data-image-large-src"]
            picture_urls.append(picture_url)

        condition = "https://schema.org/RefurbishedCondition"

        return Product(
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
            condition=condition,
        )
