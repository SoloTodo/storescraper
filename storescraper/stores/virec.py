from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy
from storescraper.categories import (
    HEADPHONES,
    MONITOR,
    TELEVISION,
    STORAGE_DRIVE,
    MEMORY_CARD,
    UPS,
)


class Virec(StoreWithUrlExtensions):
    url_extensions = [
        ["auriculares", HEADPHONES],
        ["monitores", MONITOR],
        ["televisores", TELEVISION],
        ["discos-duros", STORAGE_DRIVE],
        ["memorias-micro-sd", MEMORY_CARD],
        ["ups", UPS],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://www.virec.cl/categoria-producto/{}/page/{}/".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("li", "product-type-simple")
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
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
        json_tag = soup.find("script", {"type": "application/ld+json"})
        json_data = json.loads(json_tag.text)
        name = json_data["name"]
        offer = json_data["offers"][0]
        price = (Decimal(offer["price"]) * Decimal("1.19")).quantize(0)
        description = json_data["description"]

        if "image" in json_data:
            picture_urls = [json_data["image"]]
        else:
            picture_urls = None

        sku = json_data["sku"]
        stock_container = soup.find("span", "stock in-stock")
        stock_number = stock_container.text.split()[0]

        if stock_number.isdigit():
            stock = int(stock_number)
        else:
            stock = -1 if offer["availability"] == "http://schema.org/InStock" else 0

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
            description=description,
            part_number=sku,
        )
        return [p]
