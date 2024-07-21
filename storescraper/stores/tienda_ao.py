import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TiendaAo(Store):
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
            if page > 10:
                raise Exception("Page overflow")
            url = "https://tiendaao.com/?paged={}&product_cat=lg".format(page)
            print(url)
            res = session.get(url, verify=False)
            soup = BeautifulSoup(res.text, "lxml")

            product_containers = soup.findAll("li", "product-item")
            if not product_containers:
                break

            for product in product_containers:
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, "lxml")
        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[-1]
        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )
        for entry in json_data["@graph"]:
            if entry["@type"] == "Product":
                product_data = entry
                break
        else:
            raise Exception("No JSON product data found")

        price = Decimal(product_data["offers"][0]["price"])
        description = product_data["description"]
        picture_urls = [product_data["image"]]
        sku = product_data["sku"]
        name = product_data["name"]

        if product_data["offers"][0]["availability"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0

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
            "COP",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=sku,
        )
        return [p]
