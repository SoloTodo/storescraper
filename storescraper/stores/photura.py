import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Photura(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            url = (
                "https://www.photura.com/collections/lg/?page={}&"
                "section_id=collection-template".format(page)
            )
            response = session.get(url)
            soup = BeautifulSoup(response.text, "lxml")
            product_tags = soup.findAll("div", "product-item")

            if not product_tags:
                if page == 1:
                    logging.warning("Empty category:")
                break

            for product_tag in product_tags:
                product_url = "https://www.photura.com" + product_tag.find("a")["href"]

                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        json_tag = soup.find("script", {"type": "application/ld+json"})
        json_data = json.loads(json_tag.text)
        name = json_data["name"]
        key = soup.find("input", {"type": "hidden", "name": "id"})["value"]
        stock = -1
        price = Decimal(json_data["offers"][0]["price"]).quantize(Decimal("0.01"))
        sku = json_data["sku"]
        picture_urls = [
            "https:" + x["href"]
            for x in soup.findAll("a", "product-gallery__thumbnail")
        ]

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
            "USD",
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
        )
        return [p]
