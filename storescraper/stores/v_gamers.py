import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    HEADPHONES,
    KEYBOARD_MOUSE_COMBO,
    KEYBOARD,
    MONITOR,
    POWER_SUPPLY,
    COMPUTER_CASE,
    MOUSE,
    GAMING_CHAIR,
    CPU_COOLER,
    VIDEO_CARD,
    STORAGE_DRIVE,
    MOTHERBOARD,
    PROCESSOR,
    RAM,
    GAMING_DESK,
    CASE_FAN,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class VGamers(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos", HEADPHONES],
        ["teclados", KEYBOARD],
        ["zona-gamer/mouse", MOUSE],
        ["escritorio", GAMING_DESK],
        ["sillas", GAMING_CHAIR],
        ["sillones", GAMING_CHAIR],
        ["zona-gamer/kit-gamer", KEYBOARD_MOUSE_COMBO],
        ["hardware/almacenamiento", STORAGE_DRIVE],
        ["hardware/fuentes-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["hardware/memorias-ram", RAM],
        ["hardware/placas-madres", MOTHERBOARD],
        ["hardware/procesadores", PROCESSOR],
        ["hardware/water-cooling", CPU_COOLER],
        ["hardware/disipador-cpu", CPU_COOLER],
        ["hardware/ventiladores", CASE_FAN],
        ["hardware/tarjetas-graficas", VIDEO_CARD],
        ["monitores", MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://vgamers.cl/categoria-producto/" "{}/page/{}/".format(
                url_extension, page
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html.parser")
            product_containers = soup.findAll("div", "product")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
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
        description = product_data["description"]
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

        picture_urls = []
        picture_container = soup.find("figure", "woocommerce-product-gallery__wrapper")
        for p in picture_container.findAll("a"):
            if p["href"] not in picture_urls:
                picture_urls.append(p["href"])

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
