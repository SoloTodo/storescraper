import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    TABLET,
    NOTEBOOK,
    MOTHERBOARD,
    PROCESSOR,
    CPU_COOLER,
    VIDEO_CARD,
    RAM,
    COMPUTER_CASE,
    POWER_SUPPLY,
    STORAGE_DRIVE,
    MONITOR,
    KEYBOARD_MOUSE_COMBO,
    MOUSE,
    KEYBOARD,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class EntrePcYWeb(StoreWithUrlExtensions):
    url_extensions = [
        ["144-notebooks", NOTEBOOK],
        ["133-almacenamiento", STORAGE_DRIVE],
        ["134-enfriamiento-pc", CPU_COOLER],
        ["135-fuentes-de-poder", POWER_SUPPLY],
        ["136-gabinetes", COMPUTER_CASE],
        ["137-memorias-ram", RAM],
        ["138-placas-madre", MOTHERBOARD],
        ["139-procesadores", PROCESSOR],
        ["140-tarjetas-de-video", VIDEO_CARD],
        ["146-kit-teclado-y-mouse", KEYBOARD_MOUSE_COMBO],
        ["149-monitores", MONITOR],
        ["150-mouse", MOUSE],
        ["151-teclados", KEYBOARD],
        ["152-tablet", TABLET],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 20:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://entrepcyweb.cl/{}?page={}".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = [
                tag
                for tag in soup.findAll("div", "item-product")
                if not tag.find("li", "out_of_stock")
            ]

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
        name = soup.find("h1", "h1").text.strip()
        desc_tag = soup.find("div", "product-information")
        key = desc_tag.find("input", {"name": "id_product"})["value"]
        stock = 0 if desc_tag.find("i", "product-unavailable") else -1
        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"]
        )
        sku = soup.find("span", {"itemprop": "sku"}).text.strip()
        picture_urls = [
            tag.find("a")["href"] for tag in soup.findAll("div", "easyzoom--overlay")
        ]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            "CLP",
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
        )
        return [p]
