import base64
import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, vtex_preflight, html_to_markdown


class MisBeneficios(Store):
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
            if offset >= 150:
                raise Exception("Page overflow")

            variables = {
                "from": offset,
                "to": offset + 15,
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
                "https://www.misbeneficios.com.uy/_v/segment/graphql/v1"
                "?extensions={}".format(json.dumps(payload))
            )
            response = session.get(endpoint).json()

            product_entries = response["data"]["productSearch"]["products"]

            if not product_entries:
                break

            for product_entry in product_entries:
                product_url = "https://www.misbeneficios.com.uy/{}/p".format(
                    product_entry["linkText"]
                )
                product_urls.append(product_url)

            offset += 15

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html5lib")

        product_data_tag = soup.find("template", {"data-varname": "__STATE__"})
        product_data = json.loads(str(product_data_tag.find("script").contents[0]))

        if not product_data:
            return []

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        key = product_specs["productId"]
        name = product_specs["productName"]
        sku = product_specs["productReference"]
        description = html_to_markdown(product_specs["description"])
        pricing_key = "${}.items.0.sellers.0.commertialOffer".format(base_json_key)
        pricing_data = product_data[pricing_key]

        uyu_price = Decimal(str(pricing_data["Price"]))
        price = (uyu_price / Decimal(extra_args["exchange_rate"])).quantize(
            Decimal("0.01")
        )

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
            description=description,
            picture_urls=picture_urls,
        )

        return [p]

    @classmethod
    def preflight(cls, extra_args=None):
        d = {}
        d.update(
            vtex_preflight(
                extra_args,
                "https://www.misbeneficios.com.uy/"
                "electronica-audio-y-video/televisores",
            )
        )

        # Exchange rate
        variables = {"acronym": "usd_quotation", "fields": ["quotation"]}

        payload = {
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "9c99c65417b4324a74eb55fc8d6792f18950e0119e3e210088765cf06b97c017",
                },
                "variables": base64.b64encode(
                    json.dumps(variables).encode("utf-8")
                ).decode("utf-8"),
            }
        }

        endpoint = "https://www.misbeneficios.com.uy/_v/private/graphql/v1"
        session = session_with_proxy(extra_args)
        session.headers["Content-Type"] = "application/json"
        response = session.post(endpoint, json=payload).json()
        d["exchange_rate"] = response["data"]["searchDocument"][0]["quotation"]
        return d
