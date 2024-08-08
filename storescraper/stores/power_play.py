from bs4 import BeautifulSoup
from decimal import Decimal
import json
import re
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import (
    PROCESSOR,
    MOTHERBOARD,
    VIDEO_CARD,
    POWER_SUPPLY,
    SOLID_STATE_DRIVE,
    COMPUTER_CASE,
    RAM,
    CPU_COOLER,
    NOTEBOOK,
    USB_FLASH_DRIVE,
    PRINTER,
    MONITOR,
    KEYBOARD,
    MOUSE,
    VIDEO_GAME_CONSOLE,
    MICROPHONE,
    HEADPHONES,
    STEREO_SYSTEM,
    GAMING_CHAIR,
)


class PowerPlay(StoreWithUrlExtensions):
    url_extensions = [
        ["video-juegos/consolas-nsw", VIDEO_GAME_CONSOLE],
        ["video-juegos/consolas-xbox-series-s-x", VIDEO_GAME_CONSOLE],
        ["video-juegos/consolas-ps3-ps4", VIDEO_GAME_CONSOLE],
        ["video-juegos/consolas-ps5", VIDEO_GAME_CONSOLE],
        ["hardware/procesadores", PROCESSOR],
        ["hardware/placas-madres", MOTHERBOARD],
        ["hardware/ram-ddr4-ddr5", RAM],
        ["hardware/almacenamiento-pc", SOLID_STATE_DRIVE],
        ["hardware/gabinetes", COMPUTER_CASE],
        ["hardware/fuentes-de-poder", POWER_SUPPLY],
        ["hardware/enfriamiento", CPU_COOLER],
        ["perifericos/microfonos", MICROPHONE],
        ["perifericos/mouse", MOUSE],
        ["perifericos/teclados", KEYBOARD],
        ["audifonos-gamer", HEADPHONES],
        ["audifonos-parlantes/audifonos-tws", HEADPHONES],
        ["audifonos-parlantes/parlantes-pc", STEREO_SYSTEM],
        ["audifonos-parlantes/parlantes-bluetooth", STEREO_SYSTEM],
        ["product-category/escritorios-sillas", GAMING_CHAIR],
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
                stock = (
                    int(re.search(r"\d+", stock_container.text).group())
                    if stock_container
                    else 0
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
