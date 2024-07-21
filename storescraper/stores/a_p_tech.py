from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    CASE_FAN,
    CELL,
    COMPUTER_CASE,
    CPU_COOLER,
    GAMING_CHAIR,
    HEADPHONES,
    KEYBOARD,
    MICROPHONE,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    NOTEBOOK,
    POWER_SUPPLY,
    PROCESSOR,
    RAM,
    SOLID_STATE_DRIVE,
    STORAGE_DRIVE,
    TABLET,
    VIDEO_CARD,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import remove_words, session_with_proxy


class APTech(StoreWithUrlExtensions):
    url_extensions = [
        ["almacenamiento/hdd-disco-duro-mecanico", STORAGE_DRIVE],
        ["almacenamiento/ssd-unidad-estado-solido", SOLID_STATE_DRIVE],
        ["celulares", CELL],
        ["fuente-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["memorias-ram", RAM],
        ["monitores", MONITOR],
        ["notebooks", NOTEBOOK],
        ["perifericos/audifonos", HEADPHONES],
        ["perifericos/microfonos", MICROPHONE],
        ["perifericos/mouse", MOUSE],
        ["perifericos/teclados", KEYBOARD],
        ["placa-madre", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["refrigeracion-y-ventilacion/disipador-cpu", CPU_COOLER],
        ["refrigeracion-y-ventilacion/refrigeracion-liquida", CPU_COOLER],
        ["refrigeracion-y-ventilacion/ventilador-gabinete", CASE_FAN],
        ["sillas", GAMING_CHAIR],
        ["tablet", TABLET],
        ["tarjeta-de-video", VIDEO_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://aptech.cl/product-category/" "{}/page/{}/".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage, timeout=60)
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
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        response = session.get(url, timeout=60)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, "lxml")
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]

        json_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )
        for entry in json_data["@graph"]:
            if entry["@type"] == "Product":
                product_data = entry
                break
        else:
            raise Exception("No JSON product data found")

        name = product_data["name"]
        sku = str(product_data["sku"])
        description = product_data["description"]

        qty_input = soup.find("input", "input-text qty text")
        if qty_input:
            if qty_input["max"]:
                stock = int(qty_input["max"])
            else:
                stock = -1
        else:
            if soup.find("button", "single_add_to_cart_button"):
                stock = 1
            else:
                stock = 0

        if soup.find("p", "price").find("ins"):
            price = Decimal(remove_words(soup.find("p", "price").find("ins").text))
        else:
            price = Decimal(remove_words(soup.find("p", "price").text))

        picture_urls = [
            tag["src"]
            for tag in soup.find("div", "woocommerce-" "product-gallery").findAll("img")
        ]
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
        )
        return [p]
