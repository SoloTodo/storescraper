import re
from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    ALL_IN_ONE,
    CELL,
    GAMING_CHAIR,
    MONITOR,
    NOTEBOOK,
    PRINTER,
    RAM,
    SOLID_STATE_DRIVE,
    TABLET,
    TELEVISION,
    STEREO_SYSTEM,
    MOUSE,
    VIDEO_CARD,
    KEYBOARD,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class NoeComputacion(StoreWithUrlExtensions):
    url_extensions = [
        ["199", ALL_IN_ONE],
        ["147", SOLID_STATE_DRIVE],
        ["233", STEREO_SYSTEM],
        ["235", NOTEBOOK],
        ["212", CELL],
        ["188", PRINTER],
        ["223", RAM],
        ["184", MONITOR],
        ["61", NOTEBOOK],
        ["228", MOUSE],
        ["215", GAMING_CHAIR],
        ["95", TABLET],
        ["231", VIDEO_CARD],
        ["227", KEYBOARD],
        ["178", TELEVISION],
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
            if page > 12:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = (
                "https://noecomputacion.com/tienda/page/{}/"
                "?filter_cat={}&_pjax=.site-content".format(page, url_extension)
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            if response.status_code == 404:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            product_containers = soup.findAll("div", "product")
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[1]

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )
        for entry in json_data["@graph"]:
            if entry["@type"] == "Product":
                product_data = entry
                break
        else:
            raise Exception("No JSON product data found")

        name = product_data["name"][:250]
        sku = str(product_data["sku"])
        description = product_data["description"]

        offer = product_data["offers"][0]
        normal_price = Decimal(offer["price"])

        offer_price_match = re.search(r"\$([\d|.]+)", description)
        if offer_price_match:
            offer_price_text = offer_price_match.groups()[0]
            offer_price = Decimal(remove_words(offer_price_text))
        else:
            offer_price = normal_price

        if offer_price > Decimal(100000000) or normal_price > Decimal(100000000):
            return []

        qty_input = soup.find("input", "input-text qty text")
        if qty_input:
            if qty_input["max"]:
                stock = int(qty_input["max"])
            else:
                stock = -1
        else:
            if soup.find("button", "single_add_to_cart_button"):
                stock = 1
            else:
                stock = 0

        picture_urls = [
            x["data-src"] for x in soup.findAll("img", "attachment-woocommerce_single")
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
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
