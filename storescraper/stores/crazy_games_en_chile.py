import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    HEADPHONES,
    COMPUTER_CASE,
    MICROPHONE,
    SOLID_STATE_DRIVE,
    RAM,
    MONITOR,
    MOUSE,
    GAMING_CHAIR,
    KEYBOARD,
    POWER_SUPPLY,
    MOTHERBOARD,
    PROCESSOR,
    STEREO_SYSTEM,
    USB_FLASH_DRIVE,
    VIDEO_CARD,
    CPU_COOLER,
    EXTERNAL_STORAGE_DRIVE,
    KEYBOARD_MOUSE_COMBO,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class CrazyGamesenChile(StoreWithUrlExtensions):
    url_extensions = [
        ["kit-gamer", KEYBOARD_MOUSE_COMBO],
        ["monitores", MONITOR],
        ["mouse-gamer", MOUSE],
        ["mouse-oficina", MOUSE],
        ["sillas-gamer", GAMING_CHAIR],
        ["teclados-gamer", KEYBOARD],
        ["teclados-oficina", KEYBOARD],
        ["audifonos-gamer", HEADPHONES],
        ["audifonos-de-musica", HEADPHONES],
        ["audifonos-home-office", HEADPHONES],
        ["microfonos-1", MICROPHONE],
        ["parlantes", STEREO_SYSTEM],
        ["discos-internos", SOLID_STATE_DRIVE],
        ["discos-externos", EXTERNAL_STORAGE_DRIVE],
        ["memorias-y-pendrive", USB_FLASH_DRIVE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["memorias-ram", RAM],
        ["placas-madres", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["tarjetas-de-video", VIDEO_CARD],
        ["ventiladores-y-refrigeracion-liquida", CPU_COOLER],
        ["pages/productos-open-box-y-segunda-seleccion", KEYBOARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        )
        product_urls = []
        page = 1

        while True:
            if page >= 20:
                raise Exception("Page overflow")

            if "/" in url_extension:
                url_webpage = "https://www.crazygamesenchile.com/{}?page={}".format(
                    url_extension, page
                )
            else:
                url_webpage = (
                    "https://www.crazygamesenchile.com/"
                    "collections/{}?page={}".format(url_extension, page)
                )
            print(url_webpage)
            res = session.get(url_webpage)

            if res.status_code == 404:
                raise Exception("Invalid category: " + url_extension)

            soup = BeautifulSoup(res.text, "lxml")
            product_containers = soup.findAll("li", "grid__item")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append("https://www.crazygamesenchile.com" + product_url)

            if "/" in url_extension:
                break

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
        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("input", {"name": "id"})["value"]

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )
        name = json_data["name"]
        sku = json_data.get("sku", None)

        if not sku:
            hidden_spans = soup.findAll("span", "visually-hidden")

            for span in hidden_spans:
                if "SKU:" in span.text and span.next_sibling:
                    sku = span.next_sibling.strip()

        description = json_data["description"]
        variants = json_data.get("hasVariant", [])

        if variants and sku:
            for variant in variants:
                if variant["sku"] == sku:
                    price = Decimal(str(variant["offers"]["price"]))
                    break
        else:
            price = Decimal(str(json_data["offers"]["price"]))

        if "disabled" in soup.find("button", "product-form__submit").attrs:
            stock = 0
        else:
            stock = -1

        picture_container = soup.find("ul", "product__media-list")
        picture_urls = []

        for a in picture_container.findAll("li"):
            picture_urls.append("https:" + a.find("img")["src"])

        if "OPEN BOX" in name.upper() or "SEGUNDA" in name.upper():
            condition = "https://schema.org/OpenBoxCondition"
        else:
            condition = "https://schema.org/NewCondition"

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
            picture_urls=picture_urls,
            description=description,
            condition=condition,
        )

        return [p]
