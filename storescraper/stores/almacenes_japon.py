import base64
import json
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import (
    html_to_markdown,
    session_with_proxy,
    vtex_preflight,
    check_ean13,
)


class AlmacenesJapon(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

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
                "https://www.almacenesjapon.com/_v/segment/graphql/v1"
                "?extensions={}".format(json.dumps(payload))
            )
            response = session.get(endpoint).json()

            product_entries = response["data"]["productSearch"]["products"]

            if not product_entries:
                break

            for product_entry in product_entries:
                product_url = "https://www.almacenesjapon.com/{}/p".format(
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
        soup = BeautifulSoup(response.text, "lxml")

        if response.status_code == 404:
            return []

        product_data = json.loads(
            soup.find("template", {"data-varname": "__STATE__"}).find("script").text
        )

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        item_key = "{}.items.0".format(base_json_key)
        key = product_data[item_key]["itemId"]
        ean = product_data[item_key]["ean"]
        if not check_ean13(ean):
            ean = None

        name = product_specs["productName"]
        sku = product_specs["productReference"]
        description = html_to_markdown(product_specs.get("description", ""))

        pricing_key = "${}.items.0.sellers.0.commertialOffer".format(base_json_key)
        pricing_data = product_data[pricing_key]

        price = Decimal(str(pricing_data["Price"])) + Decimal(str(pricing_data["Tax"]))

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
            "USD",
            sku=sku,
            ean=ean,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]

    @classmethod
    def preflight(cls, extra_args=None):
        return vtex_preflight(
            extra_args,
            "https://www.almacenesjapon.com/tecnologia/TV-y-Video/LEDS-y-Smart-TV",
        )
