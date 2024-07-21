import html
import json
import logging
import re
from collections import defaultdict
from decimal import Decimal

import requests.utils
from bs4 import BeautifulSoup

from storescraper.categories import (
    NOTEBOOK,
    VIDEO_CARD,
    PROCESSOR,
    MONITOR,
    TELEVISION,
    MOTHERBOARD,
    RAM,
    STORAGE_DRIVE,
    SOLID_STATE_DRIVE,
    POWER_SUPPLY,
    COMPUTER_CASE,
    CPU_COOLER,
    TABLET,
    PRINTER,
    CELL,
    EXTERNAL_STORAGE_DRIVE,
    USB_FLASH_DRIVE,
    MEMORY_CARD,
    PROJECTOR,
    VIDEO_GAME_CONSOLE,
    STEREO_SYSTEM,
    ALL_IN_ONE,
    MOUSE,
    OPTICAL_DRIVE,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    WEARABLE,
    UPS,
    AIR_CONDITIONER,
    GAMING_CHAIR,
    CASE_FAN,
    HEADPHONES,
    DISH_WASHER,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class PcFactory(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            VIDEO_CARD,
            PROCESSOR,
            MONITOR,
            TELEVISION,
            MOTHERBOARD,
            RAM,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            CPU_COOLER,
            TABLET,
            PRINTER,
            CELL,
            EXTERNAL_STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            PROJECTOR,
            VIDEO_GAME_CONSOLE,
            STEREO_SYSTEM,
            ALL_IN_ONE,
            MOUSE,
            OPTICAL_DRIVE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            WEARABLE,
            UPS,
            AIR_CONDITIONER,
            GAMING_CHAIR,
            CASE_FAN,
            HEADPHONES,
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_entries = defaultdict(lambda: [])

        # Productos normales
        url_extensions = [
            ["999", ALL_IN_ONE],
            ["735", NOTEBOOK],
            ["411", STORAGE_DRIVE],
            ["266", RAM],
            ["994", TABLET],
            ["418", KEYBOARD_MOUSE_COMBO],
            ["1301", KEYBOARD],
            ["1302", MOUSE],
            ["5", CELL],
            ["936", WEARABLE],
            ["1007", GAMING_CHAIR],
            ["438", VIDEO_GAME_CONSOLE],
            ["38", UPS],
            ["995", MONITOR],
            ["46", PROJECTOR],
            ["422", EXTERNAL_STORAGE_DRIVE],
            ["904", EXTERNAL_STORAGE_DRIVE],
            ["218", USB_FLASH_DRIVE],
            ["48", MEMORY_CARD],
            ["340", STORAGE_DRIVE],
            ["585", SOLID_STATE_DRIVE],
            ["421", STORAGE_DRIVE],
            ["932", STORAGE_DRIVE],
            ["262", PRINTER],
            ["789", TELEVISION],
            ["797", STEREO_SYSTEM],
            ["889", STEREO_SYSTEM],
            ["891", STEREO_SYSTEM],
            ["850", HEADPHONES],
            ["1107", DISH_WASHER],
            ["1021", AIR_CONDITIONER],
            ["272", PROCESSOR],
            ["292", MOTHERBOARD],
            ["112", RAM],
            ["100", RAM],
            ["334", VIDEO_CARD],
            ["326", COMPUTER_CASE],
            ["54", POWER_SUPPLY],
            ["647", CASE_FAN],
            ["648", CPU_COOLER],
            ["286", OPTICAL_DRIVE],
        ]

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 0
            idx = 1
            while True:
                if page > 10:
                    raise Exception("page overflow: " + url_extension)
                url_webpage = (
                    "https://integracion.pcfactory.cl/catalogo/productos/query"
                    "?size=100&categorias={}&page={}".format(url_extension, page)
                )
                print(url_webpage)
                response = session.get(url_webpage)
                json_data = response.json()
                products_data = json_data["content"]["items"]

                if not products_data:
                    if page == 0:
                        raise Exception("Empty category: " + url_extension)
                    break

                for product_entry in products_data:
                    product_url = (
                        "https://www.pcfactory.cl/producto/" + product_entry["slug"]
                    )
                    section = product_entry["categoria"]["nombre"]
                    product_entries[product_url].append(
                        {"category_weight": 1, "section_name": section, "value": idx}
                    )
                    idx += 1
                page += 1

        # Segunda seleccción
        url_extensions = [
            # ["liq-celulares", CELL],
            # ["liq-tablets", TABLET],
            # ["liq-notebook", NOTEBOOK],
            # ["liq-aio", ALL_IN_ONE],
            # ["liq-tv", TELEVISION],
            # ["liq-smart", WEARABLE],
            # ["liq-impresoras", PRINTER],
        ]

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = "https://www.pcfactory.cl/{}".format(url_extension)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product")

            if not product_containers:
                continue

            section_tag = soup.find("div", {"data-menu-categoria": url_extension})
            section = "{} > {}".format(
                html.unescape(section_tag["data-menu-path"]), section_tag["data-menu"]
            )

            for idx, container in enumerate(product_containers):
                product_url = container.find("a")["href"]
                product_entries["https://www.pcfactory.cl" + product_url].append(
                    {"category_weight": 1, "section_name": section, "value": idx + 1}
                )

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        product_id_match = re.search(r"/producto/(\d+)", url)
        product_id = product_id_match.groups()[0]
        # Specs
        res = session.get(
            "https://integracion.pcfactory.cl/catalogo/productos/" + product_id
        )
        product_data = res.json()
        sku = str(product_data["id"])
        part_number = product_data["partNumber"]

        if part_number:
            part_number = part_number.strip()

        name = product_data["nombre"]

        # Precio
        res = session.get(
            "https://integracion.pcfactory.cl/catalogo/productos/{}/precio".format(
                product_id
            )
        )
        price_data = res.json()

        normal_price = Decimal(price_data["precio"]["normal"])
        offer_price = Decimal(price_data["precio"]["efectivo"])

        # Stock
        res = session.get(
            "https://integracion.pcfactory.cl/catalogo/productos/{}/stock".format(
                product_id
            )
        )
        stock_data = res.json()
        stock = 0
        for zona in stock_data["disponibilidad"]:
            for sucursal in zona["sucursales"]:
                stock += int(sucursal["aproximado"].replace("+", ""))

        # Pictures
        res = session.get(
            "https://integracion.pcfactory.cl/catalogo/productos/{}/imagenes".format(
                product_id
            )
        )
        pictures_data = res.json()
        picture_urls = [x["sizes"]["0"] for x in pictures_data["imagenes"]]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            "CLP",
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls,
        )
        return [p]
