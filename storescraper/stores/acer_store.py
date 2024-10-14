import base64
import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal
from storescraper.categories import (
    MONITOR,
    NOTEBOOK,
    MOUSE,
    HEADPHONES,
    TABLET,
    WEARABLE,
)

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import (
    session_with_proxy,
    html_to_markdown,
)


class AcerStore(StoreWithUrlExtensions):
    url_extensions = [
        ["monitores", MONITOR],
        ["outlet-monitores-pc", MONITOR],
        ["mouse", MOUSE],
        ["headset", HEADPHONES],
        ["notebook-gamer", NOTEBOOK],
        ["notebook", NOTEBOOK],
        ["outlet-notebook-tradicional", NOTEBOOK],
        ["outlet-notebook-gamer", NOTEBOOK],
        ["outlet-ultralivianos", NOTEBOOK],
        ["tablets", TABLET],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        product_urls = []
        session = session_with_proxy(extra_args)
        page = 1

        while True:
            url = f"https://acerstore.cl/collections/{url_extension}?page={page}"
            print(url)

            response = session.get(url)
            soup = BeautifulSoup(response.text, "lxml")
            products = soup.findAll("div", "product-card-wrapper")

            if not products:
                if page == 1:
                    raise Exception(f"Empty category: {url_extension}")
                break

            for product in products:
                product_url = product.find("a")["href"]
                product_urls.append(f"https://www.acerstore.cl{product_url}")

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        product_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )

        name = product_data["name"]
        sku = product_data["sku"]
        part_number = product_data["category"]
        description = html_to_markdown(soup.find("p", "product__text").text)
        description_lower = description.lower()
        name_lower = name.lower()

        if (
            "outlet" in description_lower
            or "outlet" in name_lower
            or "seminuevo" in description_lower
            or "seminuevo" in name_lower
        ):
            if "openbox" in description_lower or "open box" in description_lower:
                condition = "https://schema.org/OpenBoxCondition"
            else:
                condition = "https://schema.org/RefurbishedCondition"
        else:
            condition = "https://schema.org/NewCondition"

        offer = product_data["offers"]
        price = Decimal(offer["price"])
        key = offer["url"].split("?variant=")[1]
        stock = -1 if offer["availability"] == "http://schema.org/InStock" else 0
        pictures_container = soup.find("div", "grid__item product__media-wrapper")
        picture_urls = list(
            set(
                f"https:{img['src'].split('?')[0]}"
                for img in pictures_container.findAll("img")
            )
        )

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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls,
            condition=condition,
        )

        return [p]
