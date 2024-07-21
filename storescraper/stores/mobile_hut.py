import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.utils import session_with_proxy
from storescraper.categories import (
    CELL,
    HEADPHONES,
    MOUSE,
    WEARABLE,
    STEREO_SYSTEM,
    TABLET,
    MONITOR,
    KEYBOARD,
    USB_FLASH_DRIVE,
)
from storescraper.store_with_url_extensions import StoreWithUrlExtensions


class MobileHut(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos", HEADPHONES],
        ["tws", HEADPHONES],
        ["parlantes", STEREO_SYSTEM],
        ["smartphones", CELL],
        ["wearables", WEARABLE],
        ["almacenamiento", USB_FLASH_DRIVE],
        ["teclados-1", KEYBOARD],
        ["mouses", MOUSE],
        ["monitores", MONITOR],
        ["teclados", KEYBOARD],
        ["mouse-gamer", MOUSE],
        ["tablets", TABLET],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 30:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://www.mobilehut.cl/collections/{}?page={}".format(
                url_extension, page
            )
            res = session.get(url_webpage)
            soup = BeautifulSoup(res.text, "lxml")
            product_containers = soup.findAll("div", "pr_grid_item")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_slug = container.find("a")["href"].split("/")[-1]
                product_url = "https://www.mobilehut.cl/products/" + product_slug
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        variants_tag = soup.find("select", "product-form__variants").findAll("option")
        variants_match = re.search(r'"productVariants":(.+)},},', response.text)
        print(variants_match.groups()[0])
        variants_data = json.loads(variants_match.groups()[0])

        assert len(variants_tag) == len(variants_data)
        products = []

        for variant_tag, variant_entry in zip(variants_tag, variants_data):
            print(variant_entry)
            name = "{} ({})".format(
                variant_entry["product"]["title"], variant_entry["title"]
            )
            key = variant_entry["id"]
            if "nt_sold_out" in variant_tag.attrs.get("class", ""):
                stock = 0
            else:
                stock = -1
            price = Decimal(variant_entry["price"]["amount"])
            if variant_entry["image"]:
                picture_urls = ["https:" + variant_entry["image"]["src"]]
            else:
                picture_urls = []
            sku = variant_entry["sku"]

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
            )
            products.append(p)
        return products
