from decimal import Decimal
import logging

from bs4 import BeautifulSoup
from storescraper.categories import *
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class TechMark(StoreWithUrlExtensions):
    url_extensions = [
        ["notebook-gamer", NOTEBOOK],
        ["notebook-calidad-empresa", NOTEBOOK],
        ["smartphone-android", CELL],
        ["iphone", CELL],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["tablet-ipad", TABLET],
        ["macbook-imac", NOTEBOOK],
        ["productos-gigabyte", MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://www.tiendatechmark.cl/{}?page={}".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-block")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = (
                    "https://www.tiendatechmark.cl" + container.find("a")["href"]
                )
                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        sku_tag = soup.find("span", "sku_elem")

        if not sku_tag:
            return []

        sku = sku_tag.text.strip()
        key = soup.find("meta", {"property": "og:id"})["content"]
        name = soup.find("h1", "page-header").text.strip()
        availability_tag = soup.find("meta", {"property": "product:availability"})
        stock = -1 if availability_tag["content"] == "instock" else 0
        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"]
        )
        picture_urls = [
            x.find("img")["src"] for x in soup.findAll("div", "carousel-item")
        ]
        description = soup.find("meta", {"name": "description"})["content"]

        if "USADO" in description.upper():
            condition = "https://schema.org/UsedCondition"
        else:
            condition = "https://schema.org/RefurbishedCondition"

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
            condition=condition,
        )
        return [p]
