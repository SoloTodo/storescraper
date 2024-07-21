import json
import logging
from bs4 import BeautifulSoup
from decimal import Decimal
from storescraper.categories import TELEVISION

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Hiraoka(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow")

            category_url = (
                "https://hiraoka.com.pe/catalogsearch/result/"
                "index/?q=LG+LG&p={}".format(page)
            )
            print(category_url)
            res = session.get(category_url)
            soup = BeautifulSoup(res.text, "lxml")

            product_containers = soup.find("div", "products")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category")
                break

            for p in product_containers.findAll("li", "product"):
                product_url = p.find("a")["href"]
                if product_url in product_urls:
                    return product_urls
                product_urls.append(product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        soup = BeautifulSoup(session.get(url).content, "lxml")

        product_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )

        name = product_data["name"]
        sku = product_data["sku"]
        price = Decimal(product_data["offers"]["price"])

        if soup.find("button", "tocart"):
            stock = -1
        else:
            stock = 0

        if soup.find("td", {"data-th": "Modelo"}):
            part_number = soup.find("td", {"data-th": "Modelo"}).text
        else:
            part_number = None

        picture_container = soup.find("div", "fotorama__stage")
        picture_urls = []
        if picture_container:
            for i in picture_container.findAll("img"):
                picture_urls.append(i["src"])
        else:
            picture_urls = [product_data["image"]]

        description = html_to_markdown(
            soup.find("div", "hiraoka-product-details-datasheet").text
        )

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
            "PEN",
            sku=sku,
            description=description,
            picture_urls=picture_urls,
            part_number=part_number,
        )

        return [p]
