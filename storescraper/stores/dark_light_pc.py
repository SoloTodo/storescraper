import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    COMPUTER_CASE,
    RAM,
    SOLID_STATE_DRIVE,
    MOTHERBOARD,
    PROCESSOR,
    POWER_SUPPLY,
    VIDEO_CARD,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class DarkLightPc(StoreWithUrlExtensions):
    url_extensions = [
        ["componentes/tarjeta-grafica", VIDEO_CARD],
        ["componentes/ram", RAM],
        ["componentes/almacenamiento", SOLID_STATE_DRIVE],
        ["componentes/placa-madre", MOTHERBOARD],
        ["componentes/procesador", PROCESSOR],
        ["componentes/fte-poder", POWER_SUPPLY],
        ["componentes/gabinete", COMPUTER_CASE],
        ["perifericos/teclados-mecanicos", PROCESSOR],
        ["perifericos/mouse", PROCESSOR],
        ["perifericos/audifonos", PROCESSOR],
        ["perifericos/parlantes", PROCESSOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = (
                "https://darklightpc.cl/product-category/"
                "{}/page/{}/".format(url_extension, page)
            )
            print(url_webpage)
            response = session.get(url_webpage, timeout=60)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-grid-item")

            if not product_containers:
                if page == 1:
                    logging.warning("empty category: " + url_extension)
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
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        response = session.get(url, timeout=60)
        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", "product_title").text
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
        sku = soup.find("span", "sku").text.strip()

        if soup.find("button", "single_add_to_cart_button"):
            stock = -1
        else:
            stock = 0

        if soup.find("p", "price").find("ins"):
            offer_price = Decimal(
                remove_words(soup.find("p", "price").find("ins").text)
            )
        else:
            offer_price = Decimal(remove_words(soup.find("p", "price").text))

        normal_price = (offer_price * Decimal("1.038")).quantize(0)

        picture_urls = [
            tag["src"]
            for tag in soup.find("div", "woocommerce-" "product-gallery").findAll("img")
        ]
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
        )
        return [p]
