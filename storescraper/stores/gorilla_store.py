import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    MOUSE,
    KEYBOARD,
    MONITOR,
    GAMING_CHAIR,
    VIDEO_CARD,
    PROCESSOR,
    MOTHERBOARD,
    POWER_SUPPLY,
    CPU_COOLER,
    STORAGE_DRIVE,
    RAM,
    COMPUTER_CASE,
    SOLID_STATE_DRIVE,
    USB_FLASH_DRIVE,
    CASE_FAN,
    NOTEBOOK,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class GorillaStore(StoreWithUrlExtensions):
    url_extensions = [
        ["procesadores", PROCESSOR],
        ["placas-madre", MOTHERBOARD],
        ["memoria-ram", RAM],
        ["ssd", SOLID_STATE_DRIVE],
        ["pendrive-flash", USB_FLASH_DRIVE],
        ["hdd", STORAGE_DRIVE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["tarjetas-graficas", VIDEO_CARD],
        ["gabinetes", COMPUTER_CASE],
        ["watercooling", CPU_COOLER],
        ["disipacion-por-aire", CPU_COOLER],
        ["ventiladores", CASE_FAN],
        ["monitores", MONITOR],
        ["teclado", KEYBOARD],
        ["mouse", MOUSE],
        ["sillas-gamer", GAMING_CHAIR],
        ["notebooks", NOTEBOOK],
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
                "https://www.gorillastore.cl/index.php/"
                "product-category/{}/page/{}/".format(url_extension, page)
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("li", "type-product")
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
        name = soup.find("h2", "product_title").text.strip()
        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[1]

        add_to_cart_tag = soup.find("button", "single_add_to_cart_button")

        if add_to_cart_tag:
            stock = -1
        else:
            stock = 0

        price_tags = soup.findAll("span", "woocommerce-Price-amount")
        assert len(price_tags) == 4

        offer_price = Decimal(remove_words(price_tags[1].text))
        normal_price = Decimal(remove_words(price_tags[2].text))
        picture_urls = [tag["src"] for tag in soup.findAll("img", "post-image")]
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
        )
        return [p]
