from decimal import Decimal
import json
import logging

import validators
from bs4 import BeautifulSoup
from storescraper.categories import (
    KEYBOARD,
    MONITOR,
    NOTEBOOK,
    PROCESSOR,
    RAM,
    SOLID_STATE_DRIVE,
    TABLET,
    PRINTER,
    EXTERNAL_STORAGE_DRIVE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class Clie(StoreWithUrlExtensions):
    url_extensions = [
        ["impresoras", PRINTER],
        ["teclados", KEYBOARD],
        ["monitores", MONITOR],
        ["notebooks", NOTEBOOK],
        ["tablets", TABLET],
        ["almacenamiento", EXTERNAL_STORAGE_DRIVE],
        ["componentes", PROCESSOR],
        ["memoria-ram-servidor", RAM],
        ["disco-duro-para-servidor", SOLID_STATE_DRIVE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = (
                "https://www.clie.cl/index.php/categoria-producto/{}/page/{}/".format(
                    url_extension, page
                )
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "html.parser")
            product_containers = soup.findAll("li", "type-product")

            if not product_containers:
                if page == 1:
                    logging.warning("empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a", "woocommerce-LoopProduct-link")[
                    "href"
                ]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=60)
        soup = BeautifulSoup(response.text, "html.parser")

        product_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )["@graph"][1]
        name = product_data["name"]
        key = str(product_data["sku"])
        offer = product_data["offers"][0]
        stock = -1 if offer["availability"] == "http://schema.org/InStock" else 0
        offer_price = Decimal(offer["price"])
        normal_price = (offer_price * Decimal("1.03")).quantize(0)
        picture_urls = (
            [product_data["image"]] if validators.url(product_data["image"]) else None
        )
        description = product_data["description"]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            "CLP",
            sku=key,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
