import base64
import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal
from storescraper.categories import TELEVISION

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import (
    check_ean13,
    session_with_proxy,
    remove_words,
    vtex_preflight,
)


class TiendasMetro(Store):
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
            if offset >= 120:
                raise Exception("Page overflow")

            variables = {
                "hideUnavailableItems": True,
                "from": offset,
                "to": offset + 12,
                "selectedFacets": [{"key": "brand", "value": "lg"}],
                "fullText": "lg",
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
                "https://www.tiendasmetro.co/_v/segment/graphql/v1"
                "?extensions={}".format(json.dumps(payload))
            )
            response = session.get(endpoint).json()

            product_entries = response["data"]["productSearch"]["products"]

            if not product_entries:
                break

            for product_entry in product_entries:
                product_url = "https://www.tiendasmetro.co/{}/p".format(
                    product_entry["linkText"]
                )
                product_urls.append(product_url)

            offset += 12

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html5lib")
        runtime_match = re.search("__RUNTIME__ = (.+)", response.text)
        runtime_json = json.loads(runtime_match.groups()[0])

        product_data_tag = soup.find("template", {"data-varname": "__STATE__"})
        product_data = json.loads(str(product_data_tag.find("script").contents[0]))

        if not product_data:
            return []

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]
        key = runtime_json["route"]["params"]["id"]
        name = product_specs["productName"]
        sku = product_specs["productReference"]
        description = product_specs.get("description", None)

        pricing_key = "${}.items.0.sellers.0.commertialOffer".format(base_json_key)
        pricing_data = product_data[pricing_key]

        price = Decimal(str(pricing_data["Price"]))

        if not price:
            pricing_key = "{}.specificationGroups.2.specifications.0".format(
                base_json_key
            )
            price = Decimal(remove_words(product_data[pricing_key]["name"]))

        stock = pricing_data["AvailableQuantity"]
        picture_list_key = "{}.items.0".format(base_json_key)
        picture_list_node = product_data[picture_list_key]
        picture_ids = [x["id"] for x in picture_list_node["images"]]

        picture_urls = []
        for picture_id in picture_ids:
            picture_node = product_data[picture_id]
            picture_urls.append(picture_node["imageUrl"].split("?")[0])

        ean = None
        for property in product_specs["properties"]:
            if product_data[property["id"]]["name"] == "EAN":
                ean = product_data[property["id"]]["values"]["json"][0]
                if check_ean13(ean):
                    break
                else:
                    ean = None

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
            ean=ean,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]

    @classmethod
    def preflight(cls, extra_args=None):
        return vtex_preflight(
            extra_args, "https://www.tiendasmetro.co/televisores-y-audio/television"
        )
