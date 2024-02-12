import json
from decimal import Decimal
import logging

from bs4 import BeautifulSoup

from storescraper.categories import (
    ALL_IN_ONE,
    NOTEBOOK,
    SOLID_STATE_DRIVE,
    STORAGE_DRIVE,
    POWER_SUPPLY,
    COMPUTER_CASE,
    MOTHERBOARD,
    PROCESSOR,
    VIDEO_CARD,
    RAM,
    TABLET,
    HEADPHONES,
    MOUSE,
    KEYBOARD,
    MONITOR,
    PRINTER,
    USB_FLASH_DRIVE,
    STEREO_SYSTEM,
    VIDEO_GAME_CONSOLE,
    GAMING_CHAIR,
    CPU_COOLER,
    KEYBOARD_MOUSE_COMBO,
    EXTERNAL_STORAGE_DRIVE,
    MEMORY_CARD,
    VACUUM_CLEANER,
    TELEVISION,
    CELL,
    WEARABLE,
    CASE_FAN,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class Todoclick(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos-over-ear-513", HEADPHONES],
        ["parlantes-gamer-514", STEREO_SYSTEM],
        ["audifonos-in-ear-552", HEADPHONES],
        ["audifonos-earbuds-556", HEADPHONES],
        ["sillas-gamer-524", GAMING_CHAIR],
        ["sillon-gamer-670", GAMING_CHAIR],
        ["kit-gamer-532", KEYBOARD_MOUSE_COMBO],
        ["consolas-571", VIDEO_GAME_CONSOLE],
        ["mouse-gamer-533", MOUSE],
        ["teclado-gamer-534", KEYBOARD],
        ["aspiradoras-619", VACUUM_CLEANER],
        ["smart-tv-643", TELEVISION],
        ["smartphones-615", CELL],
        ["smartwatch-622", WEARABLE],
        ["smart_tv-716", TELEVISION],
        ["notebooks-en-oferta-668", NOTEBOOK],
        ["all-in-one-486", ALL_IN_ONE],
        ["notebooks-483", NOTEBOOK],
        ["tablets-496", TABLET],
        ["notebooks-gamer-667", NOTEBOOK],
        ["audifono-489", HEADPHONES],
        ["teclados-554", KEYBOARD],
        ["mouse-491", MOUSE],
        ["kit-teclado-y-mouse-490", KEYBOARD_MOUSE_COMBO],
        ["soundbar-493", STEREO_SYSTEM],
        ["parlantes-485", STEREO_SYSTEM],
        ["teclado-721", KEYBOARD],
        ["disco-duro-externo-442", EXTERNAL_STORAGE_DRIVE],
        ["pendrives-443", USB_FLASH_DRIVE],
        ["tarjetas-de-memoria-444", MEMORY_CARD],
        ["ssd-unidad-de-estado-solido-445", SOLID_STATE_DRIVE],
        ["hdd-disco-duro-mecanico-555", STORAGE_DRIVE],
        ["monitor-543", MONITOR],
        ["impresoras-535", PRINTER],
        ["gabinetes-447", COMPUTER_CASE],
        ["fuentes-de-poder-446", POWER_SUPPLY],
        ["video-conferencia-701", HEADPHONES],
        ["memoria-ram-448", RAM],
        ["placa-madre-449", MOTHERBOARD],
        ["procesadores-450", PROCESSOR],
        ["refrigeracion-liquida-473", CPU_COOLER],
        ["ventiladores-pc-474", CASE_FAN],
        ["tarjetas-de-video-549", VIDEO_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page >= 15:
                raise Exception("Page overflow")

            page_url = "https://www.todoclick.cl/{}?page={}".format(url_extension, page)

            print(page_url)
            response = session.get(page_url)

            soup = BeautifulSoup(response.text, "html.parser")
            products_container = soup.find("div", {"id": "box-product-grid"})

            if not products_container:
                if page == 1:
                    logging.warning("Empty category: " + page_url)
                break

            for product in products_container.findAll("div", "item"):
                product_urls.append(product.find("a")["href"])

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        for r in response.history:
            if r.status_code == 301:
                return []
        soup = BeautifulSoup(response.text, "html5lib")
        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].string
        )

        if "offers" not in json_data:
            return []

        name = json_data["name"]
        key = soup.find("input", {"name": "_ets_cfu_product_id"})["value"]
        sku = json_data["sku"]
        offer_price = Decimal(json_data["offers"]["price"])
        normal_price = (offer_price * Decimal("1.05")).quantize(0)
        picture_urls = json_data["offers"]["image"]
        description = json_data["description"]

        if json_data["offers"]["availability"] == "https://schema.org/InStock":
            stock = -1
        else:
            stock = 0

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
