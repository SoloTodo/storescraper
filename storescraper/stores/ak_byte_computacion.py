from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    CASE_FAN,
    COMPUTER_CASE,
    HEADPHONES,
    KEYBOARD,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    POWER_SUPPLY,
    PROCESSOR,
    RAM,
    STORAGE_DRIVE,
    VIDEO_CARD,
    ALL_IN_ONE,
    NOTEBOOK,
    GAMING_CHAIR,
    PRINTER,
    TABLET,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class AkByteComputacion(StoreWithUrlExtensions):
    url_extensions = [
        ["all-in-one", ALL_IN_ONE],
        ["monitores", MONITOR],
        ["notebook", NOTEBOOK],
        ["impresoras", PRINTER],
        ["tablet", TABLET],
        ["almacenamiento", STORAGE_DRIVE],
        ["fuente-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["memorias-ram", RAM],
        ["placa-madre", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["tarjetas-graficas", VIDEO_CARD],
        ["ventiladores-y-enfriamiento-liquido", CASE_FAN],
        ["audifonos", HEADPHONES],
        ["mouses", MOUSE],
        ["sillas-gamer", GAMING_CHAIR],
        ["teclados", KEYBOARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://www.akbytecomputacion.cl/categoria-producto/{}/page/{}/".format(
                url_extension, page
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("div", "product")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a")["href"]
                print(product_url)
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
            soup.find("script", {"type": "application/ld+json"}).text
        )

        for entry in json_data["@graph"]:
            if entry["@type"] == "Product":
                product_data = entry
                break
        else:
            return []

        name = product_data["name"]
        description = product_data.get("description", None)

        if "offers" not in product_data:
            return []

        offer_price = Decimal(product_data["offers"]["price"])
        normal_price = (offer_price * Decimal("1.025")).quantize(0)

        if soup.find("p", "out-of-stock"):
            stock = 0
        elif soup.find("p", "in-stock"):
            stock = int(soup.find("p", "in-stock").text.split(" disponible")[0])
        else:
            stock = -1

        picture_urls = []
        picture_container = soup.find("figure", "woocommerce-product-gallery__wrapper")
        for i in picture_container.findAll("img"):
            picture_urls.append(i["src"])

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
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
