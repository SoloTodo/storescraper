import logging

import pyjson5
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    NOTEBOOK,
    MONITOR,
    EXTERNAL_STORAGE_DRIVE,
    MOUSE,
    HEADPHONES,
    RAM,
    ALL_IN_ONE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class Syd(StoreWithUrlExtensions):
    url_extensions = [
        ["imac", ALL_IN_ONE],
        ["macbook-air", NOTEBOOK],
        ["macbook-pro", NOTEBOOK],
        ["studio-display", MONITOR],
        ["usb-c", EXTERNAL_STORAGE_DRIVE],
        ["thunderbolt-3", EXTERNAL_STORAGE_DRIVE],
        ["ssd", EXTERNAL_STORAGE_DRIVE],
        ["raid", EXTERNAL_STORAGE_DRIVE],
        ["audio", HEADPHONES],
        ["memorias", RAM],
        ["mouse-y-teclados", MOUSE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        url_base = "https://syd.cl"
        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        )

        category_url = url_base + "/collection/" + url_extension

        response = session.get(category_url)

        if response.url != category_url:
            raise Exception("Invalid category: " + category_url)

        soup = BeautifulSoup(response.text, "lxml")
        titles = soup.findAll("div", "bs-product")

        if not titles:
            logging.warning("Empty category: " + category_url)

        for title in titles:
            product_link = title.find("a")
            product_url = url_base + product_link["href"]
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        )

        soup = BeautifulSoup(session.get(url).text, "lxml")
        json_data = pyjson5.decode(
            soup.findAll("script", {"type": "application/ld+json"})[2].text
        )
        name = json_data["name"]
        sku = json_data["sku"]
        picture_urls = json_data["image"]
        normal_price = Decimal(json_data["offers"]["price"])
        offer_price = (normal_price * Decimal("0.97")).quantize(0)
        description = json_data["description"]

        if json_data["offers"]["availability"] == "https://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            "CLP",
            sku=sku,
            part_number=sku,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
