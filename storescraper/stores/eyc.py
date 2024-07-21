import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    KEYBOARD,
    NOTEBOOK,
    TABLET,
    STORAGE_DRIVE,
    RAM,
    PROCESSOR,
    PRINTER,
    UPS,
    ALL_IN_ONE,
    MONITOR,
    MOTHERBOARD,
    POWER_SUPPLY,
    MEMORY_CARD,
    USB_FLASH_DRIVE,
    HEADPHONES,
    VIDEO_CARD,
    COMPUTER_CASE,
    SOLID_STATE_DRIVE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class Eyc(StoreWithUrlExtensions):
    url_extensions = [
        ["294-notebooks", NOTEBOOK],
        ["295-workstation", ALL_IN_ONE],
        ["313-tablet", TABLET],
        ["330-discos", STORAGE_DRIVE],
        ["306-discos", STORAGE_DRIVE],
        ["304-memorias", RAM],
        ["305-procesadores", PROCESSOR],
        ["331-impresoras", PRINTER],
        ["300-ups", UPS],
        ["339-memorias-ram", RAM],
        ["342-monitores", MONITOR],
        ["344-placas-madre", MOTHERBOARD],
        ["345-procesadores", PROCESSOR],
        ["346-fuentes-de-poder", POWER_SUPPLY],
        ["351-microsd", MEMORY_CARD],
        ["350-pendrives", USB_FLASH_DRIVE],
        ["353-audifonos", HEADPHONES],
        ["392-teclados", KEYBOARD],
        ["348-tarjetas-de-video", VIDEO_CARD],
        ["378-gabinetes", COMPUTER_CASE],
        ["395-discos-ssd", SOLID_STATE_DRIVE],
        ["361-all-in-one", ALL_IN_ONE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 20:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://tienda.eyc.cl/es/{}?page={}".format(
                url_extension, page
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            product_container = soup.findAll("article", "product-miniature")
            if not product_container:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_container:
                product_url = container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        name = (
            soup.find("div", "product-reference_top").find("span").text
            + " - "
            + soup.find("h1", "product_name").text
        )

        if "BAD BOX" in name.upper():
            condition = "https://schema.org/RefurbishedCondition"
        else:
            condition = "https://schema.org/NewCondition"

        sku = soup.find("input", {"name": "id_product"})["value"]
        part_number = soup.find("span", {"itemprop": "sku"}).text.strip()
        stock = -1
        price = Decimal(soup.find("span", "price")["content"])
        picture_urls = [
            tag["src"] for tag in soup.find("ul", "product-images").findAll("img")
        ]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            "CLP",
            sku=sku,
            picture_urls=picture_urls,
            condition=condition,
            part_number=part_number,
        )
        return [p]
