from decimal import Decimal
import json
import logging

import validators
from bs4 import BeautifulSoup
from storescraper.categories import PRINTER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Alca(Store):
    @classmethod
    def categories(cls):
        return [PRINTER]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [["solotodo", PRINTER]]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception("Page overflow: " + url_extension)
                url_webpage = "https://www.alcaplus.cl/{}/" "page/{}/".format(
                    url_extension, page
                )
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "html.parser")
                product_containers = soup.findAll("div", "product")
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

        soup = BeautifulSoup(response.text, "html.parser")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("=")[-1]

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )

        for entry in json_data["@graph"]:
            if entry["@type"] == "Product":
                product_data = entry
                break
        else:
            raise Exception("No JSON product data found")

        name = product_data["name"]
        sku = product_data["sku"][:50]
        description = product_data["description"]
        price = Decimal(product_data["offers"][0]["price"])

        stock_button = soup.find("button", {"name": "add-to-cart"})
        if stock_button:
            stock = -1
        else:
            stock = 0

        picture_urls = []
        picture_container = soup.find("figure", "product-gallery-slider")
        for i in picture_container.findAll("a"):
            if validators.url(i["href"]):
                picture_urls.append(i["href"])

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
