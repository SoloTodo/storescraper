import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    MONITOR,
    STORAGE_DRIVE,
    RAM,
    UPS,
    SOLID_STATE_DRIVE,
    EXTERNAL_STORAGE_DRIVE,
    MEMORY_CARD,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class VideoVision(StoreWithUrlExtensions):
    url_extensions = [
        ["monitores-accesorios-cctv", MONITOR],
        ["discos-duros-accesorios", STORAGE_DRIVE],
        ["discos-duros-ssd-internos", SOLID_STATE_DRIVE],
        ["disco-duro-ssd-externo", EXTERNAL_STORAGE_DRIVE],
        ["disco-duro-videovigilancia", STORAGE_DRIVE],
        ["memorias", RAM],
        ["memorias-notebook", RAM],
        ["memorias-pc", RAM],
        ["micro-sd", MEMORY_CARD],
        ["ups", UPS],
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
                "https://videovision.cl/categoria-producto/"
                "{}/page/{}/".format(url_extension, page)
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "html.parser")
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

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[-1]

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )

        name = json_data["name"]
        sku = json_data["sku"]
        part_number = json_data["description"]
        stock_span = soup.find("span", "in-stock")
        if stock_span:
            stock = int(stock_span.find("span", "stock").text.split(" ")[0])
        else:
            stock = 0
        price = Decimal(json_data["offers"][0]["price"])
        price = (price * Decimal("1.19")).quantize(0)
        picture_urls = [json_data["image"]]
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
            part_number=part_number,
            picture_urls=picture_urls,
        )
        return [p]
