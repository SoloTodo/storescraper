import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    HEADPHONES,
    KEYBOARD,
    POWER_SUPPLY,
    COMPUTER_CASE,
    MOUSE,
    CPU_COOLER,
    VIDEO_CARD,
    MOTHERBOARD,
    PROCESSOR,
    RAM,
    CASE_FAN,
    USB_FLASH_DRIVE,
    STEREO_SYSTEM,
    PRINTER,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class VGamers(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos-gamer", HEADPHONES],
        ["teclados-gamers", KEYBOARD],
        ["mouse-gamer", MOUSE],
        ["disipador-cpu", CPU_COOLER],
        ["water-cooling", CPU_COOLER],
        ["ventiladores", CASE_FAN],
        ["procesadores", PROCESSOR],
        ["placas-madres", MOTHERBOARD],
        ["memorias-ram", RAM],
        ["almacenamiento", USB_FLASH_DRIVE],
        ["tarjetas-graficas", VIDEO_CARD],
        ["gabinetes", COMPUTER_CASE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["audifonos-tradicionales", HEADPHONES],
        ["audifonos-bluetooth", HEADPHONES],
        ["radio-reloj", STEREO_SYSTEM],
        ["barras-de-sonido", STEREO_SYSTEM],
        ["parlantes", STEREO_SYSTEM],
        ["portables", STEREO_SYSTEM],
        ["mouse-tradicional", MOUSE],
        ["teclado-tradicional", KEYBOARD],
        ["impresoras-y-suministros", PRINTER],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        product_urls = []
        page = 1

        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)

            url_webpage = "https://vgamers.cl/categoria-producto/{}/page/{}/".format(
                url_extension, page
            )
            print(url_webpage)

            response = session.get(url_webpage)

            if response.status_code == 404:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break

            soup = BeautifulSoup(response.text, "lxml")
            products_container = soup.find("div", "products")

            for product in products_container.find_all("div", "product"):
                product_url = product.find("a")["href"]
                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )
        for entry in json_data["@graph"]:
            if entry["@type"] == "Product":
                product_data = entry
                break
        else:
            raise Exception("No JSON product data found")

        name = product_data["name"]
        sku = product_data["sku"]
        description = product_data.get("description", None)
        offer_price = Decimal(product_data["offers"]["price"])
        normal_price = (offer_price * Decimal(1.05)).quantize(Decimal(0))

        if not soup.find("button", "single_add_to_cart_button"):
            stock = 0
        else:
            qty_input = soup.find("input", "qty")
            if qty_input["type"] == "hidden":
                stock = 1
            elif "max" in qty_input.attrs and qty_input["max"] != "":
                stock = int(qty_input["max"])
            else:
                stock = -1

        picture_urls = [soup.find("meta", {"property": "og:image"})["content"]]

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
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
