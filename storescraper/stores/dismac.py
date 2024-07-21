from decimal import Decimal
import json
import logging

from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, magento_picture_urls


class Dismac(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        session.headers["x-algolia-api-key"] = (
            "ZDFkYTRkNWE1YzY3ODkzMjlhZjA3MzhhZTg4MTI2MzZlYzNiZT"
            "BkYjRkMDA2OGU4MDAwMGEyNDFiNzliNmZmOXRhZ0ZpbHRlcnM9"
        )
        session.headers["x-algolia-application-id"] = "BJPB6CPN3G"
        product_urls = []

        page = 0
        while True:
            print(page)
            if page > 10:
                raise Exception("page overflow")

            body = json.dumps(
                {
                    "requests": [
                        {
                            "indexName": "dis_prod_scz_products",
                            "params": "query=LG&page={}".format(page),
                        }
                    ]
                }
            )
            url_webpage = "https://bjpb6cpn3g-dsn.algolia.net/1/indexes/" "*/queries"
            response = session.post(url_webpage, data=body)
            product_json = response.json()["results"][0]["hits"]
            if not product_json:
                if page == 1:
                    logging.warning("empty site")
                break
            for product in product_json:
                product_url = product["url"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("input", {"name": "product"})["value"]

        json_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )

        name = json_data["name"]
        sku = json_data["sku"]
        description = json_data.get("description", None)
        if "price" in json_data["offers"]:
            price = Decimal(json_data["offers"]["price"])
        else:
            price = Decimal(json_data["offers"]["offers"][0]["price"])

        if not price:
            return []

        if soup.find("button", {"id": "product-addtocart-button"}):
            stock = -1
        else:
            stock = 0

        picture_urls = magento_picture_urls(soup)

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
            "BOB",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
