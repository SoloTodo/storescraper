from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    HEADPHONES,
    KEYBOARD,
    MONITOR,
    MOUSE,
    SOLID_STATE_DRIVE,
    STEREO_SYSTEM,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy


class Ibeam(StoreWithUrlExtensions):
    url_extensions = [
        ["monitores", MONITOR],
        ["disco-ssd", SOLID_STATE_DRIVE],
        ["audifonos", HEADPHONES],
        ["mouses", MOUSE],
        ["teclados", KEYBOARD],
        ["audifonos-earphones", HEADPHONES],
        ["parlantes-bluetooth", STEREO_SYSTEM],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://ibeam.cl/collections/{}/" "?page={}".format(
                url_extension, page
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html.parser")
            product_container = soup.find("ul", "productgrid--items")
            if not product_container:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_container.findAll("li"):
                product_url = container.find("a", "productitem--image-link")["href"]
                product_urls.append("https://ibeam.cl" + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        json_data = json.loads(
            soup.find("script", {"data-section-type": "static-product"}).text
        )
        product_data = json_data["product"]

        description = html_to_markdown(product_data["description"])
        picture_urls = []
        for image in product_data.get("media", []):
            if "src" in image:
                picture_urls.append("https:" + image["src"])

        products = []
        for variant in product_data["variants"]:
            key = str(variant["id"])
            name = variant["name"]
            sku = variant["sku"]
            if variant["available"]:
                stock = -1
            else:
                stock = 0

            price = (Decimal(variant["price"]) / Decimal(100)).quantize(0)

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
                sku=sku,
                picture_urls=picture_urls,
                description=description,
            )
            products.append(p)
        return products
