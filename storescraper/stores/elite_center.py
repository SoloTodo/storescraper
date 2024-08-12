import json
import logging
import re
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.categories import (
    HEADPHONES,
    SOLID_STATE_DRIVE,
    MOUSE,
    KEYBOARD,
    CPU_COOLER,
    COMPUTER_CASE,
    POWER_SUPPLY,
    RAM,
    MONITOR,
    MOTHERBOARD,
    PROCESSOR,
    VIDEO_CARD,
    STEREO_SYSTEM,
    STORAGE_DRIVE,
    VIDEO_GAME_CONSOLE,
    GAMING_CHAIR,
    NOTEBOOK,
    EXTERNAL_STORAGE_DRIVE,
    ALL_IN_ONE,
    TABLET,
    TELEVISION,
    MEMORY_CARD,
    USB_FLASH_DRIVE,
    KEYBOARD_MOUSE_COMBO,
    UPS,
    PRINTER,
    CELL,
    WEARABLE,
)
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy


class EliteCenter(StoreWithUrlExtensions):
    url_extensions = [
        ["todo-en-uno", ALL_IN_ONE],
        ["portatiles", NOTEBOOK],
        ["tableta", TABLET],
        ["cajas-gabinetes", COMPUTER_CASE],
        ["ventiladores-y-sistemas-de-enfriamiento", CPU_COOLER],
        ["tarjetas-madre-placas-madre", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["tarjetas-de-video", VIDEO_CARD],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["discos-de-estado-solido", SOLID_STATE_DRIVE],
        ["discos-duros-internos", STORAGE_DRIVE],
        ["discos-duros-externos", EXTERNAL_STORAGE_DRIVE],
        ["monitores-monitores", MONITOR],
        ["televisores", TELEVISION],
        ["tarjetas-de-memoria-flash", MEMORY_CARD],
        ["modulos-ram-genericos", RAM],
        ["modulos-ram-propietarios", RAM],
        ["unidades-flash-usb", USB_FLASH_DRIVE],
        ["audifonos", HEADPHONES],
        ["parlantes", STEREO_SYSTEM],
        ["teclados-y-teclados-de-numeros", KEYBOARD],
        ["combos-de-teclado-y-raton", KEYBOARD_MOUSE_COMBO],
        ["ratones", MOUSE],
        ["ups-respaldo-de-energia", UPS],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["sillas", GAMING_CHAIR],
        ["impresoras-ink-jet", PRINTER],
        ["impresoras-laser", PRINTER],
        ["impresoras-multifuncionales", PRINTER],
        ["celulares-desbloqueados", CELL],
        ["trackers-de-actividad", WEARABLE],
        ["relojes", WEARABLE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 15:
                raise Exception("page overflow: " + url_extension)

            url_webpage = (
                "https://elitecenter.cl/product-category/{}/"
                "page/{}/?per_page=28".format(url_extension, page)
            )
            print(url_webpage)
            response = session.get(url_webpage)

            data = response.text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("div", "product-grid-item")

            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append(product_url)

            if not soup.find("a", "next page-numbers"):
                if not product_containers and page == 1:
                    logging.warning("Empty category: " + url_extension)
                break

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

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

        name = product_data["name"][:250]
        sku = product_data.get("sku", None)

        offer_price = Decimal(product_data["offers"]["price"]).quantize(0)
        normal_price = (offer_price * Decimal("1.05")).quantize(0)
        stock = int(re.findall(r"stock_quantity_sum\":\"(\d+)\"", response.text)[1])

        picture_urls = [
            tag["href"].split("?")[0]
            for tag in soup.find(
                "figure", "woocommerce-product-gallery__wrapper"
            ).findAll("a")
            if validators.url(tag["href"])
        ]

        description_div = soup.find("div", {"id": "tab-description"})
        if description_div:
            description = html_to_markdown(description_div.text)
        else:
            description = None

        part_number_text = soup.find("div", {"data-id": "8b2d4dd"}).text.strip()
        if part_number_text:
            part_number = part_number_text.split(": ")[1].strip()
        else:
            part_number = None

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
            part_number=part_number,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
