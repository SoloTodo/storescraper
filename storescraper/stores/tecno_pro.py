import json
import logging
import re
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import (
    STEREO_SYSTEM,
    VIDEO_GAME_CONSOLE,
    MONITOR,
    HEADPHONES,
    WEARABLE,
    VIDEO_CARD,
    PROCESSOR,
    RAM,
    COMPUTER_CASE,
    MOTHERBOARD,
    POWER_SUPPLY,
    CASE_FAN,
    CPU_COOLER,
    NOTEBOOK,
    SOLID_STATE_DRIVE,
    USB_FLASH_DRIVE,
    MEMORY_CARD,
    EXTERNAL_STORAGE_DRIVE,
    MOUSE,
    KEYBOARD,
    GAMING_CHAIR,
    KEYBOARD_MOUSE_COMBO,
    UPS,
    TABLET,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class TecnoPro(StoreWithUrlExtensions):
    url_extensions = [
        ["alexa", STEREO_SYSTEM],
        ["audifonos", HEADPHONES],
        ["tarjetas-de-video", VIDEO_CARD],
        ["procesadores", PROCESSOR],
        ["memoria-ram", RAM],
        ["gabinetes", COMPUTER_CASE],
        ["placas-madre", MOTHERBOARD],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["ventilador-pc", CASE_FAN],
        ["refrigeracion-cpu", CPU_COOLER],
        ["notebook-y-computadores", NOTEBOOK],
        ["disco-duro", SOLID_STATE_DRIVE],
        ["disco-ssd-interno", SOLID_STATE_DRIVE],
        ["pendrives", USB_FLASH_DRIVE],
        ["memorias-flash", MEMORY_CARD],
        ["discos-duros-externos", EXTERNAL_STORAGE_DRIVE],
        ["mouses", MOUSE],
        ["teclados", KEYBOARD],
        ["sillas-gamer", GAMING_CHAIR],
        ["mouses-y-teclados", KEYBOARD_MOUSE_COMBO],
        ["parlantes", STEREO_SYSTEM],
        ["ups-y-energia", UPS],
        ["monitores", MONITOR],
        ["electronica-audio-y-video", HEADPHONES],
        ["tablets", TABLET],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["apple", HEADPHONES],
        ["celulares-y-telefonia", WEARABLE],
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
            url_webpage = "https://tecnopro.cl/collections/{}/".format(url_extension)

            if page > 1:
                url_webpage += "page/{}/".format(page)

            print(url_webpage)
            response = session.get(url_webpage)

            if response.url != url_webpage:
                break

            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-grid-item")

            if not product_containers:
                if page == 1:
                    logging.warning("empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        response = session.get(url)

        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", "product_title").text.strip()

        products = []
        variations_tag = soup.find("form", "variations_form")
        if variations_tag:
            variations_container = json.loads(variations_tag["data-product_variations"])
            for variation in variations_container:
                variation_name = (
                    name + " - " + variation["attributes"]["attribute_pa_color"]
                )
                sku = str(variation["variation_id"])
                part_number = variation["sku"]
                stock = 0 if variation["max_qty"] == "" else variation["max_qty"]
                price = Decimal(variation["display_price"])
                if validators.url(variation["image"]["src"]):
                    picture_urls = [variation["image"]["src"]]
                else:
                    picture_urls = None
                p = Product(
                    variation_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    sku,
                    stock,
                    price,
                    price,
                    "CLP",
                    sku=part_number,
                    part_number=part_number,
                    picture_urls=picture_urls,
                )
                products.append(p)
        else:
            json_data = json.loads(
                soup.find("script", {"type": "application/ld+json"}).text
            )

            for entry in json_data["@graph"]:
                if entry["@type"] == "Product":
                    product_data = entry
                    break
            else:
                raise Exception("No JSON product data found")

            key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
            sku = product_data.get("sku", None)
            description = product_data.get("description", None)
            stock_tag = soup.find("p", "stock")
            stock_match = re.match(r"(\d+)", stock_tag.text)
            if stock_match:
                stock = int(stock_match.groups()[0])
            else:
                stock = 0

            normal_price = Decimal(product_data["offers"]["price"])
            offer_price = (normal_price * Decimal("0.98")).quantize(0)

            picture_urls = [
                tag.find("a")["href"]
                for tag in soup.findAll("div", "product-image-wrap")
                if validators.url(tag.find("a")["href"])
            ]

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
            products.append(p)

        return products
