from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    COMPUTER_CASE,
    CPU_COOLER,
    GAMING_CHAIR,
    HEADPHONES,
    KEYBOARD,
    MONITOR,
    POWER_SUPPLY,
    SOLID_STATE_DRIVE,
    VIDEO_CARD,
    KEYBOARD_MOUSE_COMBO,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import remove_words, session_with_proxy, html_to_markdown


class Batek(StoreWithUrlExtensions):
    url_extensions = [
        ["audio", HEADPHONES],
        ["teclados-y-mouse-de-oficina", KEYBOARD_MOUSE_COMBO],
        ["audifonos", HEADPHONES],
        ["monitores", MONITOR],
        ["mouse-gamer", MONITOR],
        ["teclados", KEYBOARD],
        ["sillas-gamer", GAMING_CHAIR],
        ["almacenamiento", SOLID_STATE_DRIVE],
        ["enfriamiento", CPU_COOLER],
        ["gabinetes", POWER_SUPPLY],  # Yes, it has power supplies
        ["gabinetes-1/Gabinete", COMPUTER_CASE],
        ["memoria-ram", COMPUTER_CASE],
        ["procesadores", COMPUTER_CASE],
        ["tarjeta-de-video", VIDEO_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://batek.cl/collections/{}?page={}".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("li", "grid__item")

            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = "https://batek.cl" + container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1").text.strip()
        key = soup.find("input", {"name": "product-id"})["value"]
        add_to_cart_button = soup.find("button", "product-form__submit")
        if not add_to_cart_button or "disabled" in add_to_cart_button.attrs:
            stock = 0
        else:
            stock = -1
        price = Decimal(remove_words(soup.find("span", "price-item--sale").text))
        picture_urls = [
            "https:" + x["src"]
            for x in soup.find("div", "product-media-modal__content").findAll("img")
        ]
        description = html_to_markdown(str(soup.find("div", "product__description")))

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
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
