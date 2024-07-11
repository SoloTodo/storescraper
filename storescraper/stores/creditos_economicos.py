import json
import logging
import re

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import TELEVISION


class CreditosEconomicos(Store):
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

            url = "https://www.crecos.com/lg?_q=lg&map=ft&page=" "{}&sc=2".format(page)
            print(url)

            soup = BeautifulSoup(session.get(url).text, "html5lib")
            product_containers = json.loads(
                "{" + re.search(r"__STATE__ = {(.+)}", soup.text).groups()[0] + "}"
            )

            r = re.compile(r"Product:sp-(\d+$)")

            product_container_keys = product_containers.keys()
            products_to_find = list(filter(r.match, product_container_keys))
            if not products_to_find:
                if page == 1:
                    logging.warning("Empty category: " + category)
                else:
                    break

            for product_key in products_to_find:
                product_url = product_containers[product_key]["link"]
                product_urls.append("https://www.crecos.com" + product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.cookies["vtex_segment"] = (
            "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZ"
            "WwiOiIyIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjpudWxsLCJ1dG1f"
            "Y2FtcGFpZ24iOm51bGwsInV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24"
            "iOm51bGwsImN1cnJlbmN5Q29kZSI6IlVTRCIsImN1cnJlbmN5U3ltYm9sIjoiJC"
            "IsImNvdW50cnlDb2RlIjoiRUNVIiwiY3VsdHVyZUluZm8iOiJlcy1FQyIsImFkb"
            "WluX2N1bHR1cmVJbmZvIjoiZXMtRUMiLCJjaGFubmVsUHJpdmFjeSI6InB1Ymxp"
            "YyJ9"
        )
        new_url = "{}?sc=2".format(url)
        response = session.get(new_url)

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html5lib")
        product_data = json.loads(
            "{" + re.search(r"__STATE__ = {(.+)}", soup.text).groups()[0] + "}"
        )

        base_json_keys = list(product_data.keys())

        if not base_json_keys:
            return []

        base_json_key = base_json_keys[0]
        product_specs = product_data[base_json_key]
        slug = product_specs["linkText"]

        # key = product_specs['productId']
        key_key = "{}.items.0".format(base_json_key)
        key = product_data[key_key]["itemId"]

        name = product_specs["productName"]
        sku = product_specs["productReference"]
        description = html_to_markdown(product_specs.get("description", None))

        pricing_key = "${}.items.0.sellers.0.commertialOffer".format(base_json_key)
        pricing_data = product_data[pricing_key]
        price = Decimal(str(pricing_data["Price"]))
        stock = pricing_data["AvailableQuantity"]

        picture_list_key = "{}.items.0".format(base_json_key)
        picture_list_node = product_data[picture_list_key]
        picture_ids = [x["id"] for x in picture_list_node["images"]]

        picture_urls = []
        for picture_id in picture_ids:
            picture_node = product_data[picture_id]
            picture_urls.append(picture_node["imageUrl"].split("?")[0])

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
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
