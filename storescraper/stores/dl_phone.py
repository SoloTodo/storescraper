import json
from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    CELL,
    HEADPHONES,
    NOTEBOOK,
    TABLET,
    WEARABLE,
    TELEVISION,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class DLPhone(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos-beats", HEADPHONES],
        ["audifonos-huawei", HEADPHONES],
        ["celulares-apple", CELL],
        ["celulares-samsung", CELL],
        ["celulares-huawei", CELL],
        ["celulares-motorola", CELL],
        ["celulares-oppo", CELL],
        ["celulares-vivo", CELL],
        ["celulares-xiaomi", CELL],
        ["ipads", TABLET],
        ["tablets-huawei", TABLET],
        ["notebooks-huawei", NOTEBOOK],
        ["notebooks-acer", NOTEBOOK],
        ["notebooks-dell", NOTEBOOK],
        ["notebooks-acer", NOTEBOOK],
        ["notebooks-apple", NOTEBOOK],
        ["smartwatch-huawei", WEARABLE],
        ["televisores-hisense", TELEVISION],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        url_webpage = "https://www.dlphone.cl/collections/{}/".format(url_extension)
        print(url_webpage)
        response = session.get(url_webpage)
        soup = BeautifulSoup(response.text, "lxml")
        product_containers = soup.findAll("li", "collection-product-card")

        if not product_containers:
            logging.warning("empty category: " + url_extension)
        for container in product_containers:
            product_url = f"https://dlphone.cl{container.find('a')['href']}"
            product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        products = []
        products_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )

        for offer in products_data["offers"]:
            name = products_data["name"]
            key = offer["url"].split("?variant=")[1]
            sku = offer["sku"]
            price = Decimal(offer["price"])
            stock = -1 if offer["availability"] == "http://schema.org/InStock" else 0
            gallery = soup.find("div", "product__main").find("div", "swiper-wrapper")
            picture_urls = (
                [f"https:{img['src']}" for img in gallery.findAll("img")]
                if gallery
                else []
            )
            description = html_to_markdown(products_data["description"])

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
                condition="https://schema.org/RefurbishedCondition",
            )
            products.append(p)

        return products
