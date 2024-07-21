import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown
from curl_cffi import requests


class DePrati(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        product_urls = []
        session = requests.Session(impersonate="chrome120")

        page = 0
        while True:
            if page >= 10:
                raise Exception("Page overflow")

            url_webpage = (
                "https://www.deprati.com.ec/search/results?q=LG&page={}".format(page)
            )
            response = session.get(url_webpage)
            json_data = response.json()

            product_containers = json_data["results"]

            if not product_containers:
                if page == 0:
                    logging.warning("Empty category")
                break

            for container in product_containers:
                product_url = container["url"]
                product_urls.append("https://www.deprati.com.ec" + product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = requests.Session(impersonate="chrome120")
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        product_json = json.loads(
            soup.find("input", {"name": "producthidden"})["value"]
        )
        name = product_json["name"]
        sku = product_json["code"]
        description = html_to_markdown(product_json["description"])
        stock = product_json["stock"]["stockLevel"]
        price = Decimal(
            product_json["price"]["formattedValue"]
            .replace("$", "")
            .replace(".", "")
            .replace(",", ".")
        )
        picture_urls = [x["url"] for x in product_json["images"]]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            "USD",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
