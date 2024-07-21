import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, MONITOR, ALL_IN_ONE, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Sicot(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            MONITOR,
            ALL_IN_ONE,
            MOUSE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["computadores/notebook-y-tablets", NOTEBOOK],
            ["computadores/desktop-aio", ALL_IN_ONE],
            ["computadores/accesorios-notebooks", MOUSE],
            ["monitores", MONITOR],
            ["tienda-online/gamer", MONITOR],
        ]

        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        )

        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception("page overflow: " + url_extension)

                url_webpage = "https://www.sicot.cl/tienda-online/{}" "?p={}".format(
                    url_extension, page
                )
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, "lxml")
                product_containers = soup.findAll("div", "jet-woo-products__item")
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
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[1]

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )

        name = json_data["name"]
        sku = str(json_data["sku"])
        description = json_data["description"]
        price = Decimal(json_data["offers"][0]["price"])

        if soup.find("button", {"name": "add-to-cart"}) and not soup.find(
            "p", "stock available-on-backorder"
        ):
            stock_p = soup.find("p", "stock in-stock")
            if stock_p:
                stock = int(stock_p.text.split("disponible")[0].strip())
            else:
                stock = -1
        else:
            stock = 0

        picture_urls = []
        picture_container = soup.find("div", "woocommerce-product-gallery__wrapper")
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
            price,
            price,
            "CLP",
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
