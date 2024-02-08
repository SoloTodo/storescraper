import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    COMPUTER_CASE,
    PROCESSOR,
    RAM,
    MOTHERBOARD,
    VIDEO_CARD,
    SOLID_STATE_DRIVE,
    CPU_COOLER,
    POWER_SUPPLY,
    KEYBOARD,
    MOUSE,
    HEADPHONES,
    GAMING_CHAIR,
    NOTEBOOK,
    MONITOR,
    KEYBOARD_MOUSE_COMBO,
    VIDEO_GAME_CONSOLE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class InvasionGamer(StoreWithUrlExtensions):
    url_extensions = [
        ["gabinetes", COMPUTER_CASE],
        ["procesadores", PROCESSOR],
        ["memorias-ram", RAM],
        ["placas-madre", MOTHERBOARD],
        ["tarjeta-de-video", VIDEO_CARD],
        ["ssd-y-almacenamiento", SOLID_STATE_DRIVE],
        ["refrigeracion", CPU_COOLER],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["teclados", KEYBOARD],
        ["mouse", MOUSE],
        ["audifonos", HEADPHONES],
        ["accesorios-y-perifericos/sillas-y-escritorios", GAMING_CHAIR],
        ["accesorios-y-perifericos/kit-gamers", KEYBOARD_MOUSE_COMBO],
        ["accesorios-y-perifericos/consolas", VIDEO_GAME_CONSOLE],
        ["portatiles", NOTEBOOK],
        ["monitores", MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://invasiongamer.com/{}?page={}".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "html.parser")
            product_containers = soup.findAll("div", "product-block")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append("https://invasiongamer.com" + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        name = soup.find("meta", {"property": "og:title"})["content"]
        key = soup.find("meta", {"property": "og:id"})["content"]
        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"]
        )

        if "PREVENTA" in name.upper():
            stock = 0
        else:
            stock_text = soup.find("meta", {"property": "product:availability"})[
                "content"
            ]
            if stock_text == "instock":
                stock = -1
            else:
                stock = 0

        if "OPEN" in name.upper():
            condition = "https://schema.org/OpenBoxCondition"
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
            price,
            price,
            "CLP",
            sku=key,
            condition=condition,
        )
        return [p]
