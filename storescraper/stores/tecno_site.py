import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    CPU_COOLER,
    COMPUTER_CASE,
    GAMING_CHAIR,
    TABLET,
    NOTEBOOK,
    VIDEO_CARD,
    POWER_SUPPLY,
    RAM,
    MOTHERBOARD,
    PROCESSOR,
    KEYBOARD_MOUSE_COMBO,
    SOLID_STATE_DRIVE,
    ALL_IN_ONE,
    MOUSE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class TecnoSite(StoreWithUrlExtensions):
    url_extensions = [
        ["gamer/refrigeracion", CPU_COOLER],
        ["gamer/gabinetes", COMPUTER_CASE],
        ["gamer/mouse", MOUSE],
        ["gamer/sillas", GAMING_CHAIR],
        ["tablets-en-oferta", TABLET],
        ["portatiles/notebooks", NOTEBOOK],
        ["pc-escritorio/all-in-one", ALL_IN_ONE],
        ["componentes/bundles", VIDEO_CARD],
        ["componentes/fuentes", POWER_SUPPLY],
        ["componentes/gabinete", COMPUTER_CASE],
        ["componentes/memorias", RAM],
        ["componentes/placas-madre", MOTHERBOARD],
        ["componentes/procesador", PROCESSOR],
        ["componentes/kit-procesadores", PROCESSOR],
        ["componentes/tarjetas-de-video", VIDEO_CARD],
        ["componentes/almacenamiento", SOLID_STATE_DRIVE],
        ["accesorios/kit-tecl", KEYBOARD_MOUSE_COMBO],
        ["accesorios/perifericos", KEYBOARD_MOUSE_COMBO],
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
                "https://tienda.tecno-site.com/product-"
                "category/{}/page/{}/".format(url_extension, page)
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("li", "product")

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

        if not soup.find("span", {"id": "final-price"}):
            return []

        name = soup.find("h1", "product_title").text.strip()[:250]
        part_number_tag = soup.find("span", "sku")

        if part_number_tag:
            part_number = part_number_tag.text
        else:
            part_number = None

        sku = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[-1]

        stock_tag = soup.find("input", {"name": "quantity"})
        if stock_tag:
            if "max" in stock_tag.attrs:
                if stock_tag["max"]:
                    stock = int(stock_tag["max"])
                else:
                    stock = -1
            else:
                stock = 1
        else:
            stock = 0

        if name.startswith("("):
            condition = "https://schema.org/RefurbishedCondition"
        else:
            condition = "https://schema.org/NewCondition"

        price = Decimal(soup.find("span", {"id": "final-price"}).text.replace(".", ""))
        picture_urls = [
            tag["src"]
            for tag in soup.find("div", "woocommerce" "-product-" "gallery").findAll(
                "img"
            )
            if "No-Disponible" not in tag["src"]
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
            part_number=part_number,
            picture_urls=picture_urls,
            condition=condition,
        )
        return [p]
