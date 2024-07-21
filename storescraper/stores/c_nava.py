from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    ALL_IN_ONE,
    CASE_FAN,
    COMPUTER_CASE,
    CPU_COOLER,
    EXTERNAL_STORAGE_DRIVE,
    GAMING_CHAIR,
    HEADPHONES,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    MEMORY_CARD,
    MICROPHONE,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    NOTEBOOK,
    POWER_SUPPLY,
    PRINTER,
    PROCESSOR,
    RAM,
    SOLID_STATE_DRIVE,
    STEREO_SYSTEM,
    STORAGE_DRIVE,
    TABLET,
    USB_FLASH_DRIVE,
    VIDEO_CARD,
    UPS,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy


class CNava(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            MOTHERBOARD,
            PROCESSOR,
            RAM,
            MONITOR,
            POWER_SUPPLY,
            VIDEO_CARD,
            CPU_COOLER,
            CASE_FAN,
            STEREO_SYSTEM,
            KEYBOARD_MOUSE_COMBO,
            MICROPHONE,
            MOUSE,
            HEADPHONES,
            KEYBOARD,
            PRINTER,
            MEMORY_CARD,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            NOTEBOOK,
            TABLET,
            ALL_IN_ONE,
            GAMING_CHAIR,
            UPS,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["gabinetes-pcs", COMPUTER_CASE],
            ["tarjetas-madre", MOTHERBOARD],
            ["procesadores", PROCESSOR],
            ["memorias", RAM],
            ["monitores/monitores-monitores", MONITOR],
            ["fuentes-de-poder", POWER_SUPPLY],
            ["tarjetas-de-video", VIDEO_CARD],
            ["sistemas-de-enfriamiento/refrigeracion-liquida", CPU_COOLER],
            ["sistemas-de-enfriamiento/ventiladores", CASE_FAN],
            ["accesorios-de-todo/parlantes", STEREO_SYSTEM],
            ["perifericos/kit-teclado-y-mouse", KEYBOARD_MOUSE_COMBO],
            ["perifericos/microfonos", MICROPHONE],
            ["perifericos/mouse", MOUSE],
            ["perifericos/audio", HEADPHONES],
            ["perifericos/teclados", KEYBOARD],
            ["impresoras-y-multifuncionales/impresoras", PRINTER],
            ["impresoras-y-multifuncionales/multifuncionales", PRINTER],
            ["almacenamiento/tarjetas-de-memoria", MEMORY_CARD],
            ["almacenamiento/disco-hdd-interno", STORAGE_DRIVE],
            ["almacenamiento/discos-externos", EXTERNAL_STORAGE_DRIVE],
            ["almacenamiento/disco-ssd-interno", SOLID_STATE_DRIVE],
            ["almacenamiento/pendrives", USB_FLASH_DRIVE],
            ["equipos/notebook", NOTEBOOK],
            ["equipos/tablets", TABLET],
            ["equipos/all-in-one", ALL_IN_ONE],
            ["hogar/sillas-gamer", GAMING_CHAIR],
            ["equipos/ups", UPS],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1
            while True:
                if page > 10:
                    raise Exception("Page overflow")

                url_webpage = (
                    "https://www.cnava.cl/product-category/{}/"
                    "page/{}/".format(url_extension, page)
                )
                print(url_webpage)
                response = session.get(url_webpage)

                data = response.text
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("=")[-1]

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
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

        p_price = soup.find("div", "product-info").findAll("div", "price-wrapper")[1]
        normal_price = Decimal(remove_words(p_price.find("span", "amount").text))

        input_qty = soup.find("input", "qty")
        if input_qty:
            if "max" in input_qty.attrs and input_qty["max"]:
                stock = int(input_qty["max"])
            else:
                stock = -1
        else:
            stock = 0

        picture_urls = []
        picture_container = soup.find("figure", "woocommerce-product-gallery__wrapper")
        for a in picture_container.findAll("a"):
            picture_urls.append(a["href"])

        if "OPEN BOX" in name.upper():
            condition = "https://schema.org/RefurbishedCondition"
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
            normal_price,
            offer_price,
            "CLP",
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
            condition=condition,
        )
        return [p]
