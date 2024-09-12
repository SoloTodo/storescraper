from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    ALL_IN_ONE,
    COMPUTER_CASE,
    EXTERNAL_STORAGE_DRIVE,
    GAMING_CHAIR,
    HEADPHONES,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    NOTEBOOK,
    POWER_SUPPLY,
    PRINTER,
    PROCESSOR,
    RAM,
    SOLID_STATE_DRIVE,
    UPS,
    VIDEO_CARD,
    STEREO_SYSTEM,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Oportutek(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            COMPUTER_CASE,
            GAMING_CHAIR,
            MOTHERBOARD,
            RAM,
            VIDEO_CARD,
            POWER_SUPPLY,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            PROCESSOR,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            HEADPHONES,
            ALL_IN_ONE,
            MONITOR,
            UPS,
            PRINTER,
            STEREO_SYSTEM,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["notebooks", NOTEBOOK],
            ["gamer/Gabinetes", COMPUTER_CASE],
            ["gamer/Sillas-Gamer", GAMING_CHAIR],
            ["gamer/Motherboard", MOTHERBOARD],
            ["gamer/Memoria-RAM", RAM],
            ["gamer/Placa-de-Video", VIDEO_CARD],
            ["gamer/Fuentes-de-Poder", POWER_SUPPLY],
            ["computacion/Interno", SOLID_STATE_DRIVE],
            ["computacion/Externo", EXTERNAL_STORAGE_DRIVE],
            ["computacion/Procesador-AMD", PROCESSOR],
            ["computacion/Procesador-Intel", PROCESSOR],
            ["perifericos/Mouse", MOUSE],
            ["computacion/Teclado", KEYBOARD],
            ["perifericos/Mouse-y-Teclado", KEYBOARD_MOUSE_COMBO],
            ["computacion/Auriculares", HEADPHONES],
            ["audio/Auriculares", HEADPHONES],
            ["audio/Parlante-JBL", STEREO_SYSTEM],
            ["computacion/All-in-One", ALL_IN_ONE],
            ["monitores", MONITOR],
            ["ups-estructura-energia", UPS],
            ["impresoras-y-accesorios", PRINTER],
        ]

        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception("Page overflow: " + url_extension)
                url_webpage = (
                    "https://www.oportutek.cl/collections/{}/"
                    "?page={}".format(url_extension, page)
                )
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "lxml")
                product_containers = soup.findAll("div", "devita-product-2")
                if not product_containers:
                    if page == 1:
                        logging.warning("Empty category: " + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find("a")["href"]
                    product_urls.append("https://www.oportutek.cl" + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )

        key = soup.find("input", {"name": "product-id"})["value"]
        name = json_data["name"]
        sku = json_data["sku"]
        description = json_data["description"]
        price = Decimal(json_data["offers"][0]["price"])

        stock_span = soup.find("span", {"id": "variant-inventory"})
        if "SIN STOCK" in stock_span.text.upper():
            stock = 0
        else:
            stock = int(stock_span.text.split(" ")[0])

        if not stock and not price:
            return []

        picture_urls = []
        picture_container = soup.find("div", {"id": "ProductThumbs"})
        if picture_container:
            for a in picture_container.findAll("a"):
                picture_urls.append("https:" + a["data-image"])
        else:
            picture_urls = [json_data["image"]]

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
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
