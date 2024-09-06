import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import (
    COMPUTER_CASE,
    CPU_COOLER,
    GAMING_CHAIR,
    HEADPHONES,
    KEYBOARD,
    MOTHERBOARD,
    MOUSE,
    POWER_SUPPLY,
    PROCESSOR,
    RAM,
    STEREO_SYSTEM,
    SOLID_STATE_DRIVE,
    VIDEO_GAME_CONSOLE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy


class PowerPlay(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos-gamer", HEADPHONES],
        ["audifonos-tws", HEADPHONES],
        ["parlantes-bluetooth", STEREO_SYSTEM],
        ["parlantes-pc", STEREO_SYSTEM],
        ["almacenamiento-pc", SOLID_STATE_DRIVE],
        ["enfriamiento", CPU_COOLER],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["placas-madres", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["ram-ddr4-ddr5", RAM],
        ["mouse", MOUSE],
        ["teclados", KEYBOARD],
        ["escritorios-sillas", GAMING_CHAIR],
        ["consolas-nsw", VIDEO_GAME_CONSOLE],
        ["consolas-ps3-ps4", VIDEO_GAME_CONSOLE],
        ["consolas-ps5", VIDEO_GAME_CONSOLE],
        ["consolas-xbox-series-s-x", VIDEO_GAME_CONSOLE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        page = 1

        while True:
            url = f"https://power-play.cl/product-category/{url_extension}/page/{page}?per_page=160"
            print(url)

            response = session.get(url)

            if response.status_code == 404:
                if page == 1:
                    raise Exception("Empty category: " + url)
                break

            soup = BeautifulSoup(response.text, "lxml")
            products = soup.findAll("div", "product-wrapper")

            for product in products:
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, "lxml")
        json_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )

        for item in json_data["@graph"]:
            if item["@type"] == "Product":
                product_data = item
                assert len(product_data["offers"]) == 1
                key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
                name = product_data["name"]
                sku = product_data["sku"]
                normal_price = Decimal(product_data["offers"][0]["price"])
                gallery = soup.find(
                    "div", "woocommerce-product-gallery__wrapper"
                ).findAll("a")
                picture_urls = [img["href"] for img in gallery]
                description = html_to_markdown(product_data["description"])
                stock_container = soup.find("div", "availability stock in-stock")

                if not stock_container:
                    stock = 0
                else:
                    stock = (
                        -1
                        if stock_container.text.strip() == "En stock"
                        else int(re.search(r"\d+", stock_container.text).group())
                    )

                p = Product(
                    name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    key,
                    stock,
                    normal_price,
                    normal_price,
                    "CLP",
                    sku=sku,
                    description=description,
                    picture_urls=picture_urls,
                )

                return [p]

        return []
