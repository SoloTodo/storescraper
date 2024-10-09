import json
import logging
import time
import re

from bs4 import BeautifulSoup

from decimal import Decimal
from storescraper.utils import html_to_markdown, remove_words


from storescraper.categories import (
    TABLET,
    HEADPHONES,
    MOUSE,
    KEYBOARD,
    MONITOR,
    MOTHERBOARD,
    RAM,
    POWER_SUPPLY,
    CPU_COOLER,
    COMPUTER_CASE,
    PROCESSOR,
    SOLID_STATE_DRIVE,
    NOTEBOOK,
    VIDEO_CARD,
    STORAGE_DRIVE,
    EXTERNAL_STORAGE_DRIVE,
    USB_FLASH_DRIVE,
    MEMORY_CARD,
    CASE_FAN,
    ALL_IN_ONE,
    KEYBOARD_MOUSE_COMBO,
    TELEVISION,
    STEREO_SYSTEM,
    UPS,
    PRINTER,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Sandos(StoreWithUrlExtensions):
    url_extensions = [
        [20, SOLID_STATE_DRIVE],
        [145, SOLID_STATE_DRIVE],
        [149, STORAGE_DRIVE],
        [147, EXTERNAL_STORAGE_DRIVE],
        [148, EXTERNAL_STORAGE_DRIVE],
        [32, USB_FLASH_DRIVE],
        [33, MEMORY_CARD],
        [7, PROCESSOR],
        [8, PROCESSOR],
        [10, MOTHERBOARD],
        [12, MOTHERBOARD],
        [15, VIDEO_CARD],
        [16, VIDEO_CARD],
        [17, VIDEO_CARD],
        [27, CPU_COOLER],
        [28, CPU_COOLER],
        [35, POWER_SUPPLY],
        [36, POWER_SUPPLY],
        [39, COMPUTER_CASE],
        [39, COMPUTER_CASE],
        [40, COMPUTER_CASE],
        [29, COMPUTER_CASE],
        [142, CASE_FAN],
        [70, ALL_IN_ONE],
        [90, ALL_IN_ONE],
        [63, NOTEBOOK],
        [64, NOTEBOOK],
        [88, NOTEBOOK],
        [66, TABLET],
        [89, TABLET],
        [76, MOUSE],
        [78, KEYBOARD],
        [80, KEYBOARD_MOUSE_COMBO],
        [180, TELEVISION],
        [169, MONITOR],
        [153, MONITOR],
        [101, MONITOR],
        [179, MONITOR],
        [182, RAM],
        [25, RAM],
        [160, HEADPHONES],
        [161, HEADPHONES],
        [162, HEADPHONES],
        [165, HEADPHONES],
        [159, STEREO_SYSTEM],
        [164, STEREO_SYSTEM],
        [121, UPS],
        [98, PRINTER],
        [125, PRINTER],
        [128, PRINTER],
        [129, PRINTER],
        [167, PRINTER],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["content-type"] = "application/json"
        page = 1
        product_urls = []

        while True:
            time.sleep(2)

            response = session.post(
                "https://sandos.cl/servicio/producto",
                data=json.dumps({"idFamilia": url_extension, "page": page, "tipo": 3}),
            )
            response = json.loads(response.text)

            products = response["resultado"]["items"]

            if products == []:
                if page == 1:
                    logging.warning(f"Empty category: {url_extension}")
                break

            product_urls += [
                f"https://sandos.cl{product['url']}" for product in products
            ]
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        name = soup.find("div", "pro-group mb-3").find("h2").text
        condition = "https://schema.org/NewCondition"

        if "OPEN BOX" in name.upper() or "OPENBOX" in name.upper():
            condition = "https://schema.org/OpenBoxCondition"
        elif "REACONDICIONADO" in name.upper() or "RE ACONDICIONADO" in name.upper():
            condition = "https://schema.org/RefurbishedCondition"

        offer_price = Decimal(
            remove_words(soup.find("ul", "pro-price mt-3").find("li").text)
        )
        normal_price = Decimal(
            remove_words(soup.find("ul", "pro-price mt-1").find("li").text)
        )
        sku = None
        part_number = None

        for row in soup.find("div", "single-product-tables").findAll("tr"):
            cells = row.find_all("td")

            if len(cells) == 1:
                continue

            label = cells[0].get_text().upper()
            value = cells[1].get_text().upper()

            if value:
                if label == "SKU":
                    sku = value
                elif label == "PART NUMBER":
                    part_number = value

        stock = 0

        for p in soup.find("div", "timer").findAll("p"):
            value = re.search(r"[\+\-]?\d+", p.get_text()).group()
            stock += int(value)

        img_tag = soup.find("img", "img-fluid image_zoom_cls-1")
        picture_urls = [f"https://sandos.cl{img_tag['src']}"] if img_tag else []
        json_description = soup.find("input", {"id": "ObjectoJSON"})
        description = None

        if json_description:
            description_data = json.loads(json_description["value"])
            description = html_to_markdown(description_data["PRODUCTO"]["descripcion"])

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
            description=description,
            condition=condition,
        )
        return [p]
