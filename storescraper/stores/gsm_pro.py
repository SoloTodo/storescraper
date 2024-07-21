import json
import logging
import re
from decimal import Decimal

import pyjson5
from bs4 import BeautifulSoup

from storescraper.categories import (
    CELL,
    HEADPHONES,
    MOUSE,
    STEREO_SYSTEM,
    USB_FLASH_DRIVE,
    VIDEO_CARD,
    VIDEO_GAME_CONSOLE,
    WEARABLE,
    COMPUTER_CASE,
    CPU_COOLER,
    PROCESSOR,
    NOTEBOOK,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy


class GsmPro(StoreWithUrlExtensions):
    url_extensions = [
        ["smartphones", CELL],
        ["celulares-gamer", CELL],
        ["audifonos-in-ear", HEADPHONES],
        ["parlantes", STEREO_SYSTEM],
        ["smartwatches", WEARABLE],
        ["audifonos-gamer", HEADPHONES],
        ["smartphones-gamer", CELL],
        ["mouses-y-teclados", MOUSE],
        ["mouses-y-teclados-gamer", MOUSE],
        ["audifonos", HEADPHONES],
        ["consolas-de-video-juegos", VIDEO_GAME_CONSOLE],
        ["gabinetes", COMPUTER_CASE],
        ["fan-cooler-para-pc", CPU_COOLER],
        ["procesadores", PROCESSOR],
        ["tarjetas-graficas-para-pc", VIDEO_CARD],
        ["memorias-usb-y-pendrives", USB_FLASH_DRIVE],
        ["laptops-gamers", NOTEBOOK],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://www.gsmpro.cl/collections/{}" "?page={}".format(
                url_extension, page
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            collection = soup.find("div", "product-list--collection")
            product_containers = collection.findAll("div", "product-item")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.findAll(
                    "button", "product-item__action-button"
                )[-1]["data-product-url"]
                product_urls.append("https://www.gsmpro.cl{}".format(product_url))
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        if extra_args and "product_blacklist" in extra_args:
            product_blacklist = extra_args["product_blacklist"]
        else:
            product_blacklist = []

        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        match = re.search(r"window.location.href = '(.+)';", response.text)
        if match:
            path = match.groups()[0]
            real_url = "https://www.gsmpro.cl/" + path
            response = session.get(real_url)

        soup = BeautifulSoup(response.text, "lxml")
        publication_data = json.loads(
            soup.find(
                "script", {"type": "application/json", "data-product-json": True}
            ).text
        )
        product_data = publication_data["product"]
        publication_id = product_data["id"]
        stock_data = publication_data["inventories"]

        description = html_to_markdown(product_data["description"])
        picture_urls = ["https:" + i for i in product_data["images"]]

        products = []
        for variant in product_data["variants"]:
            key = str(variant["id"])
            name = variant["name"]
            sku = variant["sku"]
            offer_price = (Decimal(variant["price"]) / Decimal(100)).quantize(0)
            normal_price = (offer_price * Decimal("1.0356")).quantize(0)

            if publication_id in product_blacklist:
                stock = 0
            else:
                stock = max(stock_data[key]["inventory_quantity"], 0)

            variant_url = "{}?variant={}".format(url, key)

            if "SIN CAJA" in name.upper():
                name += (
                    ' - Para procesadores "sin caja" por favor dejarlos como Nuevos y asociarlos a la '
                    'variante "Tray" del procesador'
                )

            p = Product(
                name,
                cls.__name__,
                category,
                variant_url,
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
            products.append(p)

        return products

    @classmethod
    def preflight(cls, extra_args=None):
        session = session_with_proxy(extra_args)
        config = session.get(
            "https://cdn.shopify.com/s/files/1/0448/8921/1040/t/28/assets/"
            "bss-file-configdata.js"
        ).text.split("\n")[0]
        json_body = config[16:-1]
        json_data = pyjson5.decode(json_body)

        blacklist = [
            86207,  # Preventa
            75352,  # En transito
            64852,  # Descontinuado
            63078,  # Stock en transito
            63069,  # Encargo
            63064,  # Encargo
            63062,  # Stock en transito
        ]

        product_blacklist = []
        for entry in json_data:
            if entry["label_id"] in blacklist:
                product_blacklist.extend(entry["product"].split(","))

        new_extra_args = extra_args or {}
        new_extra_args["product_blacklist"] = list(set(product_blacklist))

        return new_extra_args
