import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    MOUSE,
    KEYBOARD,
    MONITOR,
    HEADPHONES,
    KEYBOARD_MOUSE_COMBO,
    COMPUTER_CASE,
    RAM,
    GAMING_CHAIR,
    STEREO_SYSTEM,
    TABLET,
    EXTERNAL_STORAGE_DRIVE,
    VIDEO_CARD,
    MOTHERBOARD,
    SOLID_STATE_DRIVE,
    POWER_SUPPLY,
    CPU_COOLER,
    MEMORY_CARD,
    ALL_IN_ONE,
    NOTEBOOK,
    WEARABLE,
    UPS,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class GGames(StoreWithUrlExtensions):
    url_extensions = [
        ["mouse", MOUSE],
        ["monitores", MONITOR],
        ["headsets", HEADPHONES],
        ["lifestyle", HEADPHONES],
        ["sillas-gamers", GAMING_CHAIR],
        ["accesorios-gamer", MONITOR],
        ["teclado", KEYBOARD],
        ["combos", KEYBOARD_MOUSE_COMBO],
        ["parlantes-1", STEREO_SYSTEM],
        ["smart-home/asistente-de-voz", STEREO_SYSTEM],
        ["componentes-pc/fuente-de-poder", POWER_SUPPLY],
        ["tarjetas-de-video", VIDEO_CARD],
        ["refrigeracion", CPU_COOLER],
        ["almacenamiento", SOLID_STATE_DRIVE],
        ["gabinete", COMPUTER_CASE],
        ["memoria-sd", MEMORY_CARD],
        ["placa-madre", MOTHERBOARD],
        ["memoria-ram", RAM],
        ["all-in-one", ALL_IN_ONE],
        ["notebook", NOTEBOOK],
        ["tablet", TABLET],
        ["accesorio-homeoffice", NOTEBOOK],
        ["hd-portatil", EXTERNAL_STORAGE_DRIVE],
        ["smart-home/smartwatch", WEARABLE],
        ["ups", UPS],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        )
        product_urls = []
        page = 1
        while True:
            if page > 40:
                raise Exception("page overflow: " + url_extension)

            url_webpage = "https://ggames.cl/collections/{}?page={}".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)

            data = response.text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("div", "product-card")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append("https://ggames.cl" + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html5lib")
        picture_urls = [
            "http:" + tag["src"].split("?v")[0]
            for tag in soup.find("div", "product-single")
            .find("div", "grid__item")
            .findAll("img")
            if tag.has_attr("src")
        ]
        text_stock = soup.find("dl", "price").text.strip().upper()
        if "AGOTADO" in text_stock or "CONSULTAR" in text_stock:
            stock = 0
        else:
            stock = -1
        json_container = json.loads(
            soup.find("script", {"id": "ProductJson-product-template"}).string.strip()
        )
        products = []
        name = json_container["title"]

        for variant in json_container["variants"]:
            variant_name = "{} {}".format(name, variant["title"]).strip()
            part_number_tag = variant["sku"]
            if part_number_tag:
                part_number = part_number_tag.strip() or None
            else:
                part_number = None
            key = str(variant["id"])
            sku = str(variant["sku"])
            price = Decimal(variant["price"] / 100)

            # https://ggames.cl/collections/headsets/products/
            # audifonos-thrustmaster-t-racing-scud-ferrari
            if price > Decimal("10000000"):
                continue

            p = Product(
                variant_name,
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
                picture_urls=picture_urls,
            )
            products.append(p)
        return products
