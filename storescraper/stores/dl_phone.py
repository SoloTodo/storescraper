import json
from decimal import Decimal
import logging
import re
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
        ["collections/audifonos-beats", HEADPHONES],
        ["collections/audifonos-huawei", HEADPHONES],
        ["collections/celulares-apple", CELL],
        ["collections/celulares-samsung", CELL],
        ["collections/celulares-huawei", CELL],
        ["collections/celulares-motorola", CELL],
        ["collections/celulares-oppo", CELL],
        ["collections/celulares-vivo", CELL],
        ["collections/celulares-xiaomi", CELL],
        ["collections/ipads", TABLET],
        ["collections/tablets-huawei", TABLET],
        ["collections/notebooks-huawei", NOTEBOOK],
        ["collections/notebooks-acer", NOTEBOOK],
        ["collections/notebooks-dell", NOTEBOOK],
        ["collections/notebooks-acer", NOTEBOOK],
        ["collections/notebooks-apple", NOTEBOOK],
        ["collections/smartwatch-huawei", WEARABLE],
        ["collections/televisores-hisense", TELEVISION],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        url_webpage = "https://www.dlphone.cl/{}/".format(url_extension)
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
            regular_price = soup.find("s", "price-item price-item--regular").text
            price = Decimal("".join(re.findall(r"\d+", regular_price)))
            offer_price = Decimal(int(offer["price"]))
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
                offer_price,
                "CLP",
                sku=sku,
                picture_urls=picture_urls,
                description=description,
                condition="https://schema.org/RefurbishedCondition",
            )
            products.append(p)

        return products
