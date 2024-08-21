import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import (
    CELL,
    COMPUTER_CASE,
    HEADPHONES,
    KEYBOARD,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    NOTEBOOK,
    POWER_SUPPLY,
    PROCESSOR,
    SOLID_STATE_DRIVE,
    SPACE_HEATER,
    TABLET,
    TELEVISION,
    VIDEO_GAME_CONSOLE,
    WEARABLE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy


class Diayta(StoreWithUrlExtensions):
    url_extensions = [
        ["audio", HEADPHONES],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["electrodomesticos", SPACE_HEATER],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["memoria", SOLID_STATE_DRIVE],
        ["monitores", MONITOR],
        ["mouse", MOUSE],
        ["notebook", NOTEBOOK],
        ["placa-madre", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["smartphone", CELL],
        ["smartwatch", WEARABLE],
        ["sunixus", HEADPHONES],
        ["tablet", TABLET],
        ["teclados", KEYBOARD],
        ["televisores", TELEVISION],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)

            url_webpage = f"https://diayta.com/collections/{url_extension}?page={page}"
            print(url_webpage)

            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-item")

            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_webpage)
                break

            for container in product_containers:
                product_url = "https://diayta.com" + container.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        product_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )
        products = []

        for offer in product_data["offers"]:
            name = product_data["name"]

            if len(product_data["offers"]) > 1:
                name = f"{name} - {offer['name']}"

            key = offer["url"].split("?variant=")[1]
            buy_button = soup.find("button", "product-form__add-button")

            if (
                buy_button.text == "Reservar"
                or offer["availability"] == "https://schema.org/OutOfStock"
            ):
                stock = 0
            elif offer["availability"] == "https://schema.org/InStock":
                stock = -1

            price = Decimal(offer["price"])

            if price == 0:
                continue

            pictures_container = soup.find("div", "product-gallery__carousel-wrapper")
            picture_urls = [
                f"https:{img['src'].split('?v')[0]}"
                for img in pictures_container.findAll("img")
            ]
            description = html_to_markdown(product_data["description"])

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
                description=description,
            )

            products.append(p)

        return products
