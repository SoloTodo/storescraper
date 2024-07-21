import json
import logging
import re
import urllib
from decimal import Decimal

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Panafoto(Store):
    endpoint = (
        "https://wlt832ea3j-dsn.algolia.net/1/indexes/*/queries?"
        "x-algolia-agent=Algolia%20for%20vanilla%20"
        "JavaScript%20(lite)%203.27.0%3Binstantsearch.js%20"
        "2.10.2%3BMagento2%20integration%20(1.10.0)%3BJS%20"
        "Helper%202.26.0&x-algolia-application-id=WLT832EA3J&x-alg"
        "olia-api-key=NzQyZDYyYTYwZGRiZDBjNjg0YjJmZDEyNWMyMTAyNTNh"
        "MjBjMDJiNzBhY2YyZWVjYWNjNzVjNjU5M2M5ZmVhY3RhZ0ZpbHRlcnM9"
    )

    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["Content-Type"] = "application/x-www-form-urlencoded"

        product_urls = []

        if category != TELEVISION:
            return []

        page = 0

        while True:
            payload_params = (
                "page={}&facetFilters={}&numericFilters=%5B"
                "%22visibility_catalog%3D1%22%5D"
                "".format(page, urllib.parse.quote('[["manufacturer:LG"]]'))
            )

            payload = {
                "requests": [
                    {
                        "indexName": "wwwpanafotocom_default_products",
                        "params": payload_params,
                    }
                ]
            }

            response = session.post(cls.endpoint, data=json.dumps(payload))
            products_json = json.loads(response.text)["results"][0]["hits"]

            if not products_json:
                if page == 0:
                    logging.warning("Empty category:")
                break

            for product_json in products_json:
                product_url = product_json["url"]
                if isinstance(product_url, list):
                    product_url = ",".join(product_url)

                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)

        # Try and find the SKU in the URL
        match = re.search(r"(\d{6})", url)
        if match:
            query = match.groups()[0]
        else:
            # The SKU is not in the url, make a search of the whole path and
            # literally hope for the best
            parsed_url = urlparse(url)
            query = parsed_url.path

        payload_params = "query={}".format(query)

        payload = {
            "requests": [
                {
                    "indexName": "wwwpanafotocom_default_products",
                    "params": payload_params,
                }
            ]
        }

        session = session_with_proxy(extra_args)
        response = session.post(cls.endpoint, data=json.dumps(payload))
        products_json = json.loads(response.text)["results"][0]["hits"]

        url_present = False
        for product_entry in products_json:
            if product_entry["url"] == url:
                url_present = True
                break

        if url_present:
            name = product_entry["name"]
            key = product_entry["sku"]
            stock = -1 if product_entry["in_stock"] else 0
            price = Decimal(str(product_entry["price"]["USD"]["default"]))
            part_number = product_entry.get("reference", None)
            picture_urls = [product_entry["image_url"]]

            return [
                Product(
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
                    sku=key,
                    part_number=part_number,
                    picture_urls=picture_urls,
                )
            ]
        else:
            res = session.get(url)
            soup = BeautifulSoup(res.text, "lxml")
            json_data = json.loads(
                soup.find("script", {"type": "application/ld+json"}).text
            )

            name = json_data["name"]
            key = json_data["sku"]
            price = Decimal(json_data["offers"]["price"])
            stock = -1 if soup.find("button", {"id": "product-addtocart-button"}) else 0

            picture_urls = []
            for i in soup.findAll("img", "fotorama__img"):
                picture_urls.append(i["src"])

            return [
                Product(
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
                    sku=key,
                    picture_urls=picture_urls,
                )
            ]
