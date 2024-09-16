import json
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from urllib.parse import quote

from storescraper.categories import NOTEBOOK, TABLET, ALL_IN_ONE, MONITOR
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, cf_session_with_proxy


class Lenovo(StoreWithUrlExtensions):
    base_domain = "https://www.lenovo.com"
    currency = "USD"
    region_extension = ""

    url_extensions = [
        ("7ca29953-e3fd-48a9-8c04-b790cfef3842", NOTEBOOK),
        ("5efac680-d533-4fba-ad6d-28311eca5544", TABLET),
        ("738528ce-a63a-4853-9d21-ddda6bb57b14", ALL_IN_ONE),
        ("4d254d3e-4799-48c9-bb2b-b552a67c1499", MONITOR),
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers["Referer"] = "https://www.lenovo.com/"
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = 1
        while True:
            payload = {
                "pageFilterId": url_extension,
                "pageSize": 100,
                "version": "v2",
                "page": page,
                "categoryCode": "accessory",
            }

            payload_str = json.dumps(payload)
            encoded_payload = quote(payload_str)
            endpoint = "https://openapi.lenovo.com/cl/es/ofp/search/dlp/product/query/get/_tsc?subSeriesCode=&loyalty=false&pageFilterId={}&params={}".format(
                url_extension, encoded_payload
            )
            res = session.get(endpoint)
            products_data = res.json()
            product_entries = products_data["data"]["data"][0]["products"]

            if not product_entries:
                if page == 1:
                    raise Exception("Empty category: " + url_extension)
                break

            for entry in product_entries:
                subseries_code = entry.get("subseriesCode", None)
                if subseries_code:
                    product_url = "https://www.lenovo.com{}/p/{}".format(
                        cls.region_extension, subseries_code
                    )
                else:
                    product_url = "https://www.lenovo.com{}{}".format(
                        cls.region_extension, entry["url"]
                    )
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        # We use the cloudflare session because the urls with special
        # characters in Lenovo make infinite bad redirects using the default
        # session
        session = cf_session_with_proxy(extra_args)
        session.headers["Referer"] = "https://www.lenovo.com/"
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        res = session.get(url)
        soup = BeautifulSoup(res.text, "lxml")
        subseries_code = soup.find("meta", {"name": "subseriesPHcode"})[
            "content"
        ].strip()

        if subseries_code:
            return cls._products_for_url_with_subseries_code(
                session, soup, url, subseries_code, category
            )
        else:
            return cls._products_for_url_without_subseries_code(
                session, soup, url, category
            )

    @classmethod
    def _products_for_url_with_subseries_code(
        cls, session, soup, url, subseries_code, category
    ):
        form_tag = soup.find("input", "formData")

        # Obtained from SKUs that do have the formData tag
        default_page_filters = {
            NOTEBOOK: "55262423-c9c7-4e23-a79a-073ce2679bc8",
            ALL_IN_ONE: "12c2c59d-900c-4e1d-ba88-5d744b774c77",
            TABLET: "b422cb4c-ba83-4f96-95a8-82872c7f1e57",
        }

        if form_tag:
            form_data = json.loads(form_tag["value"])
            page_filter_id = form_data["facetId"]
        else:
            page_filter_id = default_page_filters[category]

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
            variant_url = "https://www.lenovo.com{}{}".format(
                cls.region_extension, entry["url"]
            )

            picture_urls = []
            for image_entry in entry.get("media", {}).get("gallery", []):
                image_url = image_entry["imageAddress"]
                if not image_url.startswith("https"):
                    image_url = "https:" + image_url
                if not validators.url(image_url):
                    continue
                picture_urls.append(image_url)

            p = Product(
                name,
                cls.__name__,
                category,
                variant_url,
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

    @classmethod
    def _products_for_url_without_subseries_code(cls, session, soup, url, category):
        product_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )
        name = product_data["name"]
        sku = product_data["sku"]
        if product_data["offers"]["availability"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0
        price = Decimal(product_data["offers"]["price"])
        picture_urls = []
        for entry in product_data["image"]:
            picture_url = entry if entry.startswith("https") else "https:" + entry
            picture_urls.append(picture_url)

        specs_endpoint = (
            "https://openapi.lenovo.com/cl/es/online/product/getTechSpecs?productNumber="
            + sku
        )
        specs_res = session.get(specs_endpoint)
        specs_json = specs_res.json()
        description = ""
        specs_root = (
            specs_json["data"]["classification"] or specs_json["data"]["tables"]
        )

        if not specs_root:
            return []

        for spec in specs_root[0]["specs"]:
            description += "{}: {}\n".format(spec["headline"], spec["text"])

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
        return [p]
