import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    SOLID_STATE_DRIVE,
    STORAGE_DRIVE,
    MOTHERBOARD,
    RAM,
    POWER_SUPPLY,
    VIDEO_CARD,
    COMPUTER_CASE,
    CPU_COOLER,
    HEADPHONES,
    KEYBOARD_MOUSE_COMBO,
    KEYBOARD,
    MOUSE,
    MONITOR,
    GAMING_CHAIR,
    PROCESSOR,
    NOTEBOOK,
    CASE_FAN,
    STEREO_SYSTEM,
    EXTERNAL_STORAGE_DRIVE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class CafeDigital(StoreWithUrlExtensions):
    url_extensions = [
        ["notebooks", NOTEBOOK],
        ["almacenamiento-pc/discos-ssd", SOLID_STATE_DRIVE],
        ["almacenamiento-pc/disco-duro-pc-hdd", STORAGE_DRIVE],
        ["almacenamiento-pc/disco-duro-externo", EXTERNAL_STORAGE_DRIVE],
        ["placas-madre", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["memorias-pc", RAM],
        ["fuentes-de-poder-certificadas", POWER_SUPPLY],
        ["tarjetas-de-video", VIDEO_CARD],
        ["gabinetes-pc", COMPUTER_CASE],
        ["refrigeracion-para-pc/cooler-cpu", CPU_COOLER],
        ["refrigeracion-para-pc/refrigeracion-liquida", CPU_COOLER],
        ["refrigeracion-para-pc/ventiladores", CASE_FAN],
        ["perifericos/audifonos", HEADPHONES],
        ["perifericos/combo-kit-teclado-mouse", KEYBOARD_MOUSE_COMBO],
        ["perifericos/teclados", KEYBOARD],
        ["perifericos/mouse", MOUSE],
        ["monitores-pc", MONITOR],
        ["sillas-gamer", GAMING_CHAIR],
        ["parlantes", STEREO_SYSTEM],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)

            url_webpage = (
                "https://cafedigital.cl/categoria-producto/{}/"
                "page/{}/".format(url_extension, page)
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("li", "product")

            if not product_containers:
                if page == 1:
                    logging.warning("Empty category" + url_extension)
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
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]

        product_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )

        if "@graph" not in product_data:
            return []

        product_data = product_data["@graph"][1]

        name = product_data["name"]
        sku = str(product_data["sku"])[:45]
        description = html_to_markdown(product_data["description"])

        if "PREVENTA" in name.upper():
            stock = 0
        elif product_data["offers"][0]["availability"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        offer_price = Decimal(product_data["offers"][0]["price"])
        normal_price = (offer_price * Decimal("1.045")).quantize(0)

        picture_urls = []
        for tag in soup.find("div", "product-gallery").findAll("img", "lazyload"):
            if tag["src"].startswith("https://"):
                picture_urls.append(tag["src"])
            else:
                picture_urls.append(tag["data-src"])
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
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
