import json
import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown

from storescraper.categories import (
    STORAGE_DRIVE,
    SOLID_STATE_DRIVE,
    POWER_SUPPLY,
    COMPUTER_CASE,
    RAM,
    MONITOR,
    MOUSE,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    MOTHERBOARD,
    PROCESSOR,
    CPU_COOLER,
    VIDEO_CARD,
    STEREO_SYSTEM,
    HEADPHONES,
    GAMING_CHAIR,
    CASE_FAN,
    NOTEBOOK,
)


class TyTGamer(StoreWithUrlExtensions):
    url_extensions = [
        ["37", VIDEO_CARD],  # Tarjetas de video
        ["129", MOTHERBOARD],  # Placas madre
        ["130", PROCESSOR],  # Procesadores
        ["26", RAM],  # Memorias
        ["82", COMPUTER_CASE],  # Gabinetes
        ["73", CASE_FAN],  # Ventiladores
        ["74", CPU_COOLER],  # Cooler Procesador
        ["76", CPU_COOLER],  # Refrigeración Líquida
        ["79", POWER_SUPPLY],  # Fuentes de poder
        ["113", STORAGE_DRIVE],  # HDD
        ["114", SOLID_STATE_DRIVE],  # SSD
        ["127", SOLID_STATE_DRIVE],  # SSD 2.5
        ["128", SOLID_STATE_DRIVE],  # SSD M.2
        ["109", NOTEBOOK],  # Notebooks
        ["47", MOUSE],  # Mouses
        ["48", KEYBOARD],  # Teclados
        ["49", KEYBOARD_MOUSE_COMBO],  # Kits
        ["94", STEREO_SYSTEM],  # Parlantes
        ["95", HEADPHONES],  # Audífonos
        ["27", MONITOR],  # Monitores y proyectores
        ["100", GAMING_CHAIR],  # Sillas y Escritorio
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
        page = 1

        while True:
            category_url = "https://tytgamer.cl/tienda/{}-?page={}".format(
                url_extension, page
            )
            print(category_url)

            if page >= 10:
                raise Exception("Page overflow: " + category_url)

            response = session.get(category_url)
            json_data = response.json()

            product_cells = json_data["products"]

            if not product_cells:
                if page == 1:
                    logging.warning("Empty category: " + category_url)
                break

            for product_cell in product_cells:
                product_url = product_cell["url"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        product_id = re.search(r"/(\d+)-", url).groups()[0]
        session = session_with_proxy(extra_args)
        session.headers[
            "Content-Type"
        ] = "application/x-www-form-urlencoded; charset=UTF-8"
        session.headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
        payload = "action=quickview&id_product={}".format(product_id)
        res = session.post(
            "https://tytgamer.cl/tienda/index.php?controller=product", payload
        )
        json_data = res.json()["product"]

        name = json_data["name"]
        key = str(json_data["id"])
        stock = json_data["embedded_attributes"]["out_of_stock"]
        normal_price = Decimal(json_data["price_amount"])
        offer_price = (normal_price * Decimal("0.95")).quantize(0)
        description = html_to_markdown(json_data["description"])
        picture_urls = [x["large"]["url"] for x in json_data["images"]]

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
            sku=key,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
