import json
import logging
import re
import urllib

from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from .mercado_libre_chile import MercadoLibreChile
from storescraper.utils import session_with_proxy, remove_words
from storescraper.categories import (
    CELL,
    HEADPHONES,
    MOUSE,
    WEARABLE,
    STEREO_SYSTEM,
    TABLET,
    MONITOR,
    KEYBOARD,
    USB_FLASH_DRIVE,
)
from storescraper.store_with_url_extensions import StoreWithUrlExtensions


class MobileHut(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos", HEADPHONES],
        ["tws", HEADPHONES],
        ["parlantes", STEREO_SYSTEM],
        ["smartphones", CELL],
        ["wearables", WEARABLE],
        ["almacenamiento", USB_FLASH_DRIVE],
        ["teclados-1", KEYBOARD],
        ["mouses", MOUSE],
        ["monitores", MONITOR],
        ["teclados", KEYBOARD],
        ["mouse-gamer", MOUSE],
        ["tablets", TABLET],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 20:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://www.mobilehut.cl/collections/{}?page={}".format(
                url_extension, page
            )
            res = session.get(url_webpage)
            soup = BeautifulSoup(res.text, "html.parser")
            product_containers = soup.findAll("div", "pr_grid_item")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = "https://www.mobilehut.cl" + container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        variants_tag = soup.find("select", "product-form__variants").findAll("option")
        assert len(variants_tag) == 1

        name = soup.find("h1", "product_title").text
        key = soup.find("span", "sku").text.strip()
        if soup.find("button", "single_add_to_cart_button"):
            stock = -1
        else:
            stock = 0
        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"].replace(
                ",", ""
            )
        )
        picture_urls = [
            "https:" + urllib.parse.quote(tag["data-src"])
            for tag in soup.findAll("div", "sp-pr-gallery__img")
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
            sku=key,
            picture_urls=picture_urls,
        )
        return [p]
