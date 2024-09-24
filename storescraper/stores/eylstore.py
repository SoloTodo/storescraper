import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    COMPUTER_CASE,
    CPU_COOLER,
    HEADPHONES,
    KEYBOARD,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    NOTEBOOK,
    POWER_SUPPLY,
    PROCESSOR,
    RAM,
    SOLID_STATE_DRIVE,
    VIDEO_CARD,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Eylstore(StoreWithUrlExtensions):
    preferred_products_for_url_concurrency = 3

    url_extensions = [
        ["audifonos", HEADPHONES],
        ["discos-nvme", SOLID_STATE_DRIVE],
        ["discos-ssd", SOLID_STATE_DRIVE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["memorias-ram", RAM],
        ["monitores", MONITOR],
        ["mouse", MOUSE],
        ["notebooks", NOTEBOOK],
        ["placas-madres", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["refrigeracion", CPU_COOLER],
        ["tarjetas-de-video", VIDEO_CARD],
        ["teclados", KEYBOARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        session.headers["Content-Type"] = (
            "application/x-www-form-urlencoded; charset=UTF-8"
        )
        product_urls = []
        page = 1

        while True:
            url = f"https://eylstore.cl/categoria-producto/{url_extension}?product-page={page}"
            print(url)
            response = session.get(url)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("li", "product")

            if not product_containers:
                if page == 1:
                    raise Exception("Empty category: " + url_extension)
                break

            for product in product_containers:
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", "product_title").text.strip()
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
        sku_tag = soup.find("span", "sku")

        if sku_tag:
            sku = soup.find("span", "sku").text.strip()
        else:
            sku = None

        if soup.find("p", "out-of-stock"):
            stock = 0
        else:
            stock = -1

        pricing_tag = soup.find("div", "wc_dynprice container")
        price_tags = pricing_tag.findAll("span", "woocommerce-Price-amount")

        if not price_tags:
            return []

        normal_price = Decimal(remove_words(price_tags[1].text))
        offer_price = Decimal(remove_words(price_tags[0].text))

        picture_urls = []
        picture_container = soup.find("div", "product-images-container")

        for a in picture_container.findAll("a"):
            picture_urls.append(a["href"])

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
            part_number=sku,
        )
        return [p]
