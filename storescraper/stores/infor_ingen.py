import json
import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    CPU_COOLER,
    MOTHERBOARD,
    PROCESSOR,
    RAM,
    STORAGE_DRIVE,
    SOLID_STATE_DRIVE,
    EXTERNAL_STORAGE_DRIVE,
    VIDEO_CARD,
    COMPUTER_CASE,
    POWER_SUPPLY,
    CASE_FAN,
    MONITOR,
    KEYBOARD_MOUSE_COMBO,
    HEADPHONES,
    USB_FLASH_DRIVE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class InforIngen(StoreWithUrlExtensions):
    url_extensions = [
        ["placas-madres", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["memorias", RAM],
        ["discos-duros-pc", STORAGE_DRIVE],
        ["discos-duros-ssd", SOLID_STATE_DRIVE],
        ["discos-externos", EXTERNAL_STORAGE_DRIVE],
        ["video", VIDEO_CARD],
        ["gabinetes", COMPUTER_CASE],
        ["fuentes-reales", POWER_SUPPLY],
        ["fuentes-genericas", POWER_SUPPLY],
        ["aire-cpu", CPU_COOLER],
        ["refrigeracion-liquida-cpu", CPU_COOLER],
        ["refrigeracion-gabinete", CASE_FAN],
        ["monitores", MONITOR],
        ["teclados-y-mouse", KEYBOARD_MOUSE_COMBO],
        ["audifonos", HEADPHONES],
        ["pendrives", USB_FLASH_DRIVE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        page = 1

        while True:
            if page >= 50:
                raise Exception("Page overflow: " + url_extension)

            url_webpage = (
                "https://store.infor-ingen.com/"
                "categoria-producto/{}/page/{}/".format(url_extension, page)
            )

            print(url_webpage)
            response = session.get(url_webpage)

            if response.status_code == 404:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break

            soup = BeautifulSoup(response.text, "lxml")
            link_containers = soup.findAll("li", "product")

            for link_container in link_containers:
                product_url = link_container.find("a")["href"]
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

        soup = BeautifulSoup(response.text, "lxml")

        json_tag = soup.find("script", {"type": "application/ld+json"})
        json_data = json.loads(json_tag.text)
        name = json_data["name"].strip()

        canonical_url_tag = soup.find(
            "link", {"rel": "alternate", "type": "application/json"}
        )
        key = canonical_url_tag["href"].split("/")[-1]
        sku = json_data["sku"]
        summary_tag = soup.find("div", "summary")
        stock_tags = summary_tag.findAll("li")[:2]  # Web and Store

        stock = 0
        for stock_tag in stock_tags:
            raw_stock_text = stock_tag.contents[1]
            stock_match = re.search(r"(\d+)", raw_stock_text)
            if stock_match:
                stock += int(stock_match.groups()[0])

        offer_price = Decimal(json_data["offers"][0]["price"])
        normal_price = (offer_price * Decimal("1.06")).quantize(0)
        description = json_data["description"]
        picture_urls = [json_data["image"]]

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
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
