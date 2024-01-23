import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    ALL_IN_ONE,
    NOTEBOOK,
    CELL,
    UPS,
    WEARABLE,
    TABLET,
    MONITOR,
    COMPUTER_CASE,
    MOTHERBOARD,
    PROCESSOR,
    RAM,
    STORAGE_DRIVE,
    EXTERNAL_STORAGE_DRIVE,
    SOLID_STATE_DRIVE,
    VIDEO_CARD,
    KEYBOARD_MOUSE_COMBO,
    MOUSE,
    KEYBOARD,
    POWER_SUPPLY,
    HEADPHONES,
    GAMING_CHAIR,
    VIDEO_GAME_CONSOLE,
    PRINTER,
    MEMORY_CARD,
    USB_FLASH_DRIVE,
    STEREO_SYSTEM,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class Infosep(StoreWithUrlExtensions):
    url_extensions = [
        ["accesorios/audifonos", HEADPHONES],
        ["accesorios/memoria-micro-sdhc", MEMORY_CARD],
        ["accesorios/parlantes", STEREO_SYSTEM],
        ["accesorios/pendrive", USB_FLASH_DRIVE],
        ["accesorios/speaker", STEREO_SYSTEM],
        ["computadores/todo-en-uno", ALL_IN_ONE],
        ["gamer/audifonos-gamer", HEADPHONES],
        ["gamer/consolas-y-video-juegos", VIDEO_GAME_CONSOLE],
        ["gamer/fuentes-gamer", POWER_SUPPLY],
        ["gamer/gabinetes-gamer", COMPUTER_CASE],
        ["gamer/monitor-gamer", MONITOR],
        ["gamer/motherboard", MOTHERBOARD],
        ["gamer/mouse-gamer", MOUSE],
        ["gamer/notebook-gaming", NOTEBOOK],
        ["gamer/sillas-gamer", GAMING_CHAIR],
        ["gamer/tarjetas-de-video-gamer", VIDEO_CARD],
        ["gamer/teclado-gamer", KEYBOARD],
        ["gamer/teclado-y-mouse-gamer", KEYBOARD_MOUSE_COMBO],
        ["impresoras/epson", PRINTER],
        ["impresoras/impresora-laser", PRINTER],
        ["impresoras/impresoras-de-tinta", PRINTER],
        ["impresoras/multifuncionales", PRINTER],
        ["impresoras/multifuncionales-laser", PRINTER],
        ["monitores", MONITOR],
        ["partes-y-piezas/almacenamiento", RAM],
        ["partes-y-piezas/disco-hdd", STORAGE_DRIVE],
        ["partes-y-piezas/discos-duros-pc", STORAGE_DRIVE],
        ["partes-y-piezas/discos-externos-25", EXTERNAL_STORAGE_DRIVE],
        ["partes-y-piezas/discos-ssd", SOLID_STATE_DRIVE],
        ["partes-y-piezas/discos-ssd-externos", EXTERNAL_STORAGE_DRIVE],
        ["partes-y-piezas/discos-ssd-internos", SOLID_STATE_DRIVE],
        ["partes-y-piezas/fuente-de-poder-pc", POWER_SUPPLY],
        ["partes-y-piezas/gabinetes", COMPUTER_CASE],
        ["partes-y-piezas/kit-teclado-y-mouse", KEYBOARD_MOUSE_COMBO],
        ["partes-y-piezas/memorias-pc-notebook", RAM],
        ["partes-y-piezas/mouse-2", MOUSE],
        ["partes-y-piezas/placas-madres", MOTHERBOARD],
        ["partes-y-piezas/procesador-intel", PROCESSOR],
        ["partes-y-piezas/procesadores-amd", PROCESSOR],
        ["partes-y-piezas/procesadores-intel", PROCESSOR],
        ["partes-y-piezas/tarjetas-de-video", VIDEO_CARD],
        ["partes-y-piezas/teclados-y-mouse", KEYBOARD_MOUSE_COMBO],
        ["partes-y-piezas/ups-respaldo-de-energia", UPS],
        ["portatiles/notebooks", NOTEBOOK],
        ["portatiles/notebook-hp", NOTEBOOK],
        ["portatiles/celulares", CELL],
        ["portatiles/reloj-inteligente", WEARABLE],
        ["portatiles/tablet", TABLET],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            if page == 1:
                url_webpage = "https://infosep.cl/categoria-producto/{}/" "".format(
                    url_extension
                )
            else:
                url_webpage = (
                    "https://infosep.cl/categoria-producto/{}/"
                    "page/{}/".format(url_extension, page)
                )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html.parser")
            product_containers = soup.find("div", "products")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers.findAll("div", "product-grid-item"):
                product_url = container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[1]
        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )

        if "@graph" not in json_data:
            return []

        json_data = json_data["@graph"][1]

        name = json_data["name"]
        sku = json_data["sku"]
        offer_price = Decimal(json_data["offers"][0]["price"])

        if not offer_price:
            return []

        normal_price = (offer_price * Decimal("1.026")).quantize(0)
        stock = (
            -1
            if (json_data["offers"][0]["availability"] == "http://schema.org/InStock")
            else 0
        )

        picture_urls = [
            tag["src"]
            for tag in soup.find("div", "woocommerce-product-gallery").findAll("img")
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
            part_number=sku,
            picture_urls=picture_urls,
        )
        return [p]
