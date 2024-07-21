from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    MOTHERBOARD,
    POWER_SUPPLY,
    PROCESSOR,
    RAM,
    SOLID_STATE_DRIVE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class TokyoTech(StoreWithUrlExtensions):
    url_extensions = [
        ["procesadores", PROCESSOR],
        ["placas-madres", MOTHERBOARD],
        ["memorias-ram", RAM],
        ["discos-solidos", SOLID_STATE_DRIVE],
        ["fuentes-de-poder", POWER_SUPPLY],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://tokyostore.cl/collections/{}?page={}".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "grid-product__image-wrapper")

            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = "https://tokyostore.cl" + container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        product_json = json.loads(soup.find("script", "mainProductJson").text)
        description = html_to_markdown(str(product_json["description"]))
        picture_urls = ["https:" + x["src"] for x in product_json["media"]]
        products = []
        for variant in product_json["variants"]:
            key = str(variant["id"])
            name = variant["name"]
            stock = -1 if variant["available"] else 0
            offer_price = Decimal(variant["price"] // 100)
            normal_price = (offer_price * Decimal("1.05")).quantize(0)

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
                description=description,
            )
            products.append(p)
        return products
