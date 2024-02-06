import json
from decimal import Decimal
from bs4 import BeautifulSoup
from requests.exceptions import TooManyRedirects

from urllib.parse import quote

from storescraper.categories import NOTEBOOK, TABLET, ALL_IN_ONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Lenovo(Store):
    base_domain = "https://www.lenovo.com"
    currency = "USD"
    region_extension = ""

    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TABLET,
            ALL_IN_ONE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ("7ca29953-e3fd-48a9-8c04-b790cfef3842", NOTEBOOK),
            ("5efac680-d533-4fba-ad6d-28311eca5544", TABLET),
            ("738528ce-a63a-4853-9d21-ddda6bb57b14", ALL_IN_ONE),
        ]
        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers["Referer"] = "https://www.lenovo.com/"
        session.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        for category_id, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1
            while True:
                payload = {
                    "pageFilterId": category_id,
                    "pageSize": 100,
                    "version": "v2",
                    "page": page,
                }

                payload_str = json.dumps(payload)
                encoded_payload = quote(payload_str)
                endpoint = "https://openapi.lenovo.com/cl/es/ofp/search/dlp/product/query/get/_tsc?subSeriesCode=&loyalty=false&params={}".format(
                    encoded_payload
                )
                res = session.get(endpoint)
                products_data = res.json()
                product_entries = products_data["data"]["data"][0]["products"]

                if not product_entries:
                    if page == 1:
                        raise Exception("Empty category: " + category_id)
                    break

                for entry in product_entries:
                    subseries_code = entry.get("subseriesCode", None)
                    if not subseries_code:
                        # print(entry["summary"])
                        continue
                    product_url = "https://www.lenovo.com{}/p/{}".format(
                        cls.region_extension, subseries_code
                    )
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["Referer"] = "https://www.lenovo.com/"
        session.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        try:
            res = session.get(url)
            soup = BeautifulSoup(res.text, "html.parser")
            form_data = json.loads(soup.find("input", "formData")["value"])
            page_filter_id = form_data["facetId"]
        except TooManyRedirects:
            page_filter_id = "55262423-c9c7-4e23-a79a-073ce2679bc8"

        subseries_code = url.split("/")[-1]
        payload = {
            "pageFilterId": page_filter_id,
            "version": "v2",
            "subseriesCode": subseries_code,
        }

        payload_str = json.dumps(payload)
        encoded_payload = quote(payload_str)
        endpoint = "https://openapi.lenovo.com/cl/es/ofp/search/dlp/product/query/get/_tsc?subSeriesCode=&loyalty=false&params={}".format(
            encoded_payload
        )
        res = session.get(endpoint)
        products_data = res.json()
        products = []

        product_entries = products_data["data"]["data"]
        if not product_entries:
            return []

        for entry in product_entries[0]["products"]:
            name = entry["productName"]
            sku = entry["productCode"]
            stock = -1 if entry["marketingStatus"] == "Available" else 0
            price = Decimal(entry["finalPrice"])
            description = entry.get("featuresBenefits", None)

            picture_urls = []
            for image_entry in entry.get("media", {}).get("gallery", []):
                image_url = image_entry["imageAddress"]
                if not image_url.startswith("https"):
                    image_url = "https:" + image_url
                picture_urls.append(image_url)

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
                "CLP",
                sku=sku,
                part_number=sku,
                description=description,
                picture_urls=picture_urls,
            )
            products.append(p)

        return products
