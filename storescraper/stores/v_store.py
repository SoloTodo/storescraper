import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    WEARABLE,
    KEYBOARD,
    STEREO_SYSTEM,
    MONITOR,
    MOUSE,
    USB_FLASH_DRIVE,
    GAMING_CHAIR,
    HEADPHONES,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class VStore(StoreWithUrlExtensions):
    url_extensions = [
        ["alamcenamiento", USB_FLASH_DRIVE],
        ["audifonos", HEADPHONES],
        ["teclados", KEYBOARD],
        ["mouse", MOUSE],
        ["monitores", MONITOR],
        ["sillas", GAMING_CHAIR],
        ["parlantes", STEREO_SYSTEM],
        ["gamer", KEYBOARD],
        ["smartwatch", WEARABLE],
        ["conexion-y-video", MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        )
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://www.vstore.cl/collections/{}?page={}".format(
                url_extension, page
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html.parser")
            product_containers = soup.findAll("div", "product-item")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append("https://www.vstore.cl" + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        foo = soup.findAll("script", {"type": "application/json"})
        json_container = json.loads(foo[-1].text.strip())["product"]
        name = json_container["title"]
        key = str(json_container["id"])
        json_product = json_container["variants"][0]
        sku = json_product["sku"]
        if json_product["available"]:
            stock = -1
        else:
            stock = 0
        price = (Decimal(json_product["price"]) / Decimal(100)).quantize(0)

        if "media" in json_container:
            picture_urls = ["https:" + m["src"] for m in json_container["media"]]
        else:
            picture_urls = None

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
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
