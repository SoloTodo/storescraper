import base64
from decimal import Decimal
import json
import logging

from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import (
    check_ean13,
    html_to_markdown,
    session_with_proxy,
    vtex_preflight,
)


class Wong(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []
        product_urls = []
        session = session_with_proxy(extra_args)

        offset = 0
        while True:
            if offset >= 100:
                raise Exception("Page overflow")

            variables = {
                "from": offset,
                "to": offset + 10,
                "selectedFacets": [{"key": "b", "value": "lg"}],
            }

            payload = {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": extra_args["sha256Hash"],
                },
                "variables": base64.b64encode(
                    json.dumps(variables).encode("utf-8")
                ).decode("utf-8"),
            }

            endpoint = (
                "https://www.wong.pe/_v/segment/graphql/v1"
                "?extensions={}".format(json.dumps(payload))
            )
            response = session.get(endpoint).json()

            product_entries = response["data"]["productSearch"]["products"]

            if not product_entries:
                break

            for product_entry in product_entries:
                product_url = "https://www.wong.pe/{}/p".format(
                    product_entry["linkText"]
                )
                product_urls.append(product_url)

            offset += 10

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, "lxml")

        product_data = json.loads(
            soup.find("template", {"data-varname": "__STATE__"}).find("script").string
        )

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        key = product_specs["productId"]
        name = product_specs["productName"]
        sku = product_specs["productReference"]
        description = product_specs.get("description", None)
        if description:
            description = html_to_markdown(description)

        key_key = "{}.items.0".format(base_json_key)

        ean = product_data[key_key].get("ean", None)

        if not check_ean13(ean):
            ean = None

        pricing_key = "${}.items.0.sellers.0.commertialOffer".format(base_json_key)
        pricing_data = product_data[pricing_key]

        price = Decimal(str(pricing_data["Price"]))

        if not price:
            return []

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
            "PEN",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            ean=ean,
        )
        return [p]

    @classmethod
    def preflight(cls, extra_args=None):
        return vtex_preflight(
            extra_args, "https://www.wong.pe/tecnologia/televisores/tv"
        )
