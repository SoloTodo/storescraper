import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    CPU_COOLER,
    CASE_FAN,
    VIDEO_CARD,
    PROCESSOR,
    MONITOR,
    NOTEBOOK,
    MOTHERBOARD,
    RAM,
    STORAGE_DRIVE,
    SOLID_STATE_DRIVE,
    POWER_SUPPLY,
    COMPUTER_CASE,
    MOUSE,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    STEREO_SYSTEM,
    HEADPHONES,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class TopPc(StoreWithUrlExtensions):
    url_extensions = [
        ["24", VIDEO_CARD],  # Tarjetas de video
        ["21", PROCESSOR],  # Procesadores
        ["78", MONITOR],  # Monitores
        ["96", NOTEBOOK],  # Notebooks
        ["22", MOTHERBOARD],  # MB
        ["23", RAM],  # RAM
        ["44", STORAGE_DRIVE],  # HDD PC
        ["45", STORAGE_DRIVE],  # HDD Notebook
        ["46", SOLID_STATE_DRIVE],  # SSD
        ["27", POWER_SUPPLY],  # Fuentes de poder
        ["26", COMPUTER_CASE],  # Gabinetes
        ["108", CPU_COOLER],  # Coolers CPU
        ["67", MOUSE],
        ["66", KEYBOARD],
        ["65", KEYBOARD_MOUSE_COMBO],
        ["100", STEREO_SYSTEM],
        ["99", HEADPHONES],
        ["109", CASE_FAN],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        product_urls = []
        session = session_with_proxy(extra_args)

        category_url = "http://www.toppc.cl/tienda/{}-".format(url_extension)

        soup = BeautifulSoup(session.get(category_url).text, "lxml")
        containers = soup.findAll("li", "ajax_block_product")

        if not containers:
            logging.warning("Empty category: " + category_url)

        for container in containers:
            product_url = container.find("a")["href"]
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, "lxml")

        name = soup.find("h1").text.strip()
        sku = soup.find("input", {"name": "id_product"})["value"].strip()

        part_number_container = soup.find("meta", {"name": "description"})

        if part_number_container:
            part_number = part_number_container["content"].strip()
            if len(part_number) >= 50:
                part_number = None
        else:
            part_number = None

        availability = soup.find("link", {"itemprop": "availability"})

        if "VENTA SOLO EN PC ARMADO" in str(soup):
            # Gabinete "VENTA SOLO EN PC ARMADO"
            stock = 0
        elif availability and availability["href"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        offer_price_tag = soup.find("span", {"id": "our_price_display"})

        if not offer_price_tag:
            return []

        offer_price = offer_price_tag.string
        offer_price = Decimal(remove_words(offer_price))

        normal_price = soup.find("p", {"id": "old_price"}).find("span", "price").string
        normal_price = Decimal(remove_words(normal_price))

        description = html_to_markdown(str(soup.find("section", "page-product-box")))

        picture_urls = [tag["href"] for tag in soup.findAll("a", "fancybox")]

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
            part_number=part_number or None,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
