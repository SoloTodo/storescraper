from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    COMPUTER_CASE,
    GAMING_CHAIR,
    HEADPHONES,
    KEYBOARD,
    MONITOR,
    MOUSE,
    POWER_SUPPLY,
    RAM,
    SOLID_STATE_DRIVE,
    VIDEO_CARD,
    PROCESSOR,
    MOTHERBOARD,
    CPU_COOLER,
    USB_FLASH_DRIVE,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy


class Tecnoaxis(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            MONITOR,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            VIDEO_CARD,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            GAMING_CHAIR,
            PROCESSOR,
            MOTHERBOARD,
            CPU_COOLER,
            USB_FLASH_DRIVE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["almacenamiento", SOLID_STATE_DRIVE],
            ["monitores", MONITOR],
            ["partes-y-piezas/fuentes-de-poder", POWER_SUPPLY],
            ["partes-y-piezas/gabinetes", COMPUTER_CASE],
            ["partes-y-piezas/memorias", RAM],
            ["partes-y-piezas/procesadores", PROCESSOR],
            ["partes-y-piezas/tarjeta-de-video", VIDEO_CARD],
            ["partes-y-piezas/tarjeta-madre", MOTHERBOARD],
            ["partes-y-piezas/ventilador-y-enfriadores", CPU_COOLER],
            ["perifericos/audifonos", HEADPHONES],
            ["perifericos/mouse", MOUSE],
            ["perifericos/teclados", KEYBOARD],
            ["sillas", GAMING_CHAIR],
            ["perifericos/pendrive", USB_FLASH_DRIVE],
        ]

        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
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
                    "https://www.tecnoaxis.cl/categoria-producto/"
                    "{}/page/{}/".format(url_extension, page)
                )
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "lxml")
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
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[0].text
        )

        for entry in json_data["@graph"]:
            if entry["@type"] == "WebPage":
                product_data = entry
                break
        else:
            raise Exception("No JSON product data found")

        name = product_data["name"]
        description = product_data["description"]

        sku = soup.find("span", "sku").text.strip()

        section = soup.find("section", "wd-negative-gap")
        normal_price = Decimal(
            remove_words(section.findAll("span", "woocommerce-Price-amount")[-1].text)
        )

        if normal_price == 0:
            return []

        price_p = soup.find("p", "price")
        if price_p.find("ins"):
            offer_price = Decimal(remove_words(price_p.find("ins").text))
        else:
            offer_price = Decimal(remove_words(price_p.find("bdi").text))

        if soup.find("button", "single_add_to_cart_button"):
            stock = -1
        else:
            stock = 0

        picture_container = soup.find("figure", "woocommerce-product-gallery__wrapper")
        picture_urls = []

        for a in picture_container.findAll("a"):
            picture_urls.append(a["href"])

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
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
