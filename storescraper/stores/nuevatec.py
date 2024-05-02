from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    CASE_FAN,
    COMPUTER_CASE,
    EXTERNAL_STORAGE_DRIVE,
    HEADPHONES,
    KEYBOARD,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    POWER_SUPPLY,
    PRINTER,
    PROCESSOR,
    RAM,
    SOLID_STATE_DRIVE,
    STORAGE_DRIVE,
    USB_FLASH_DRIVE,
    VIDEO_CARD,
    CPU_COOLER,
    MEMORY_CARD,
    STEREO_SYSTEM,
    VIDEO_GAME_CONSOLE,
    GAMING_CHAIR,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class Nuevatec(StoreWithUrlExtensions):
    url_extensions = [
        ["placas-madres", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["tarjetas-de-video", VIDEO_CARD],
        ["memorias-ram", RAM],
        ["m2-nvme", SOLID_STATE_DRIVE],
        ["ssd-2-5", SOLID_STATE_DRIVE],
        ["disco-hdd", STORAGE_DRIVE],
        ["refrigeracion-aire-cpu", CPU_COOLER],
        ["refrigeracion-liquida-cpu", CPU_COOLER],
        ["ventiladores-gabinete", CASE_FAN],
        ["gabinetes", COMPUTER_CASE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["tarjeta-sdxc", MEMORY_CARD],
        ["monitores", MONITOR],
        ["mouses-perifericos-accesorios", MOUSE],
        ["teclados-perifericos-accesorios", KEYBOARD],
        ["audifonos-perifericos-accesorios", HEADPHONES],
        ["parlantes", STEREO_SYSTEM],
        ["disco-duro-externo", EXTERNAL_STORAGE_DRIVE],
        ["pendrive", USB_FLASH_DRIVE],
        ["micro-sd", MEMORY_CARD],
        ["impresoras-scanner", PRINTER],
        ["playstation-5", VIDEO_GAME_CONSOLE],
        ["laser-printers", PRINTER],
        ["discos-duros", STORAGE_DRIVE],
        ["unidades-de-estado-solido-ssd-m2-y-nvme", SOLID_STATE_DRIVE],
        ["almacenamiento-externo", EXTERNAL_STORAGE_DRIVE],
        ["silla-gamer-accesorios-gamer-2", GAMING_CHAIR],
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
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://www.nuevatec.cl/{}/" "page/{}/".format(
                url_extension, page
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html5lib")
            product_containers = soup.findAll("div", "product-grid-item")
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
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[1]

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[0].text
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
        offer_price = Decimal(product_data["offers"][0]["price"])
        normal_price = (offer_price * Decimal(1.06)).quantize(0)

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

        picture_urls = [
            x.find("a")["href"]
            for x in soup.findAll("figure", "woocommerce-product-gallery__image")
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
        return [p]
