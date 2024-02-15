import json
import logging
import re
import urllib
from bs4 import BeautifulSoup

from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class LgV6(Store):
    base_url = "https://www.lg.com"
    region_code = property(lambda self: "Subclasses must implement this")
    currency = "USD"
    price_approximation = "0.01"
    skip_products_without_price = False
    endpoint_url = (
        "https://lgcorporationproduction0fxcu0qx.org.coveo.com/rest/search/v2"
    )

    @classmethod
    def categories(cls):
        cats = []
        for entry in cls._category_paths():
            if entry[1] not in cats:
                cats.append(entry[1])
        return cats

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = cls._category_paths()
        session = session_with_proxy(extra_args)
        session.headers["Authorization"] = "Bearer {}".format(extra_args["coveo_token"])
        discovered_urls = []

        for category_id, local_category in category_paths:
            if local_category != category:
                continue
            print(category_id)

            payload = {
                "aq": '@ec_sub_category_id=="{0}" OR @ec_category_id=="{0}"'.format(
                    category_id
                ),
                "searchHub": "{}-B2C-Listing".format(cls.region_code),
                "numberOfResults": 1000,
                "firstResult": 0,
            }

            response = session.post(cls.endpoint_url, json=payload)
            json_response = response.json()
            product_entries = json_response["results"]

            if not product_entries:
                logging.warning("Empty category: {}".format(category_id))

            for product_entry in product_entries:
                for subproduct_entry in product_entry["childResults"] + [product_entry]:
                    if cls.skip_products_without_price:
                        is_active = (
                            "ACTIVE" in subproduct_entry["raw"]["ec_model_status_code"]
                        )
                        price = Decimal(
                            subproduct_entry["raw"].get("ec_price", 0)
                        ) or Decimal(subproduct_entry["raw"].get("ec_msrp", 0))
                        if not price or not is_active:
                            continue

                    product_url = (
                        cls.base_url + subproduct_entry["raw"]["ec_model_url_path"]
                    )
                    discovered_urls.append(product_url)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        picture_urls = [
            "https://www.lg.com" + urllib.parse.quote(x["data-large-d"])
            for x in soup.find_all("a", "c-gallery__item")
            if "data-large-d" in x.attrs
        ]

        session.headers["Authorization"] = "Bearer {}".format(extra_args["coveo_token"])
        path = urllib.parse.urlparse(url).path
        payload = {
            "aq": '@ec_model_url_path=="{}"'.format(path),
            "searchHub": "{}-B2C-Listing".format(cls.region_code),
            "numberOfResults": 10,
            "firstResult": 0,
        }
        response = session.post(cls.endpoint_url, json=payload)
        json_data = response.json()["results"][0]["raw"]
        model_id = json_data["ec_model_id"]
        name = "{} - {}".format(
            json_data["ec_sales_model_code"], json_data.get("systitle", "")
        )

        # Unavailable products do not have a price, but we still need to
        # return them by default because the Where To Buy (WTB) system
        # needs to consider all products, so use zero as default.
        price = Decimal(0)
        for price_key in ["ec_price", "ec_msrp"]:
            if price_key not in json_data:
                continue
            price_value = Decimal(json_data[price_key])
            if price_value:
                price = price_value.quantize(Decimal(cls.price_approximation))
                break

        if cls.skip_products_without_price and not price:
            return []

        is_active = "ACTIVE" in json_data["ec_model_status_code"]
        is_in_stock = json_data.get("ec_stock_status", "OUT_OF_STOCK") == "IN_STOCK"

        if is_in_stock and is_active:
            stock = -1
        else:
            stock = 0

        section_path_components = []
        for i in range(1, 5):
            section_key = "ec_classification_flag_lv_{}".format(i)
            if section_key not in json_data:
                continue
            section_path_components.append(json_data[section_key])

        if section_path_components:
            section_path = " > ".join(section_path_components)
        else:
            section_path = "N/A"

        positions = [(section_path, 1)]
        sku = json_data["ec_sku"]

        raw_specs = json_data.get("ec_tech_spec_list", None)
        if raw_specs:
            raw_specs_lines = raw_specs.split(";{")
            fields = ["lv1SpecName", "lv2SpecName", "specValueName"]
            specs = []
            for line in raw_specs_lines:
                spec_line = []
                for field in fields:
                    search_query = r"{}=([\s\S]+?),".format(field)
                    match = re.search(search_query, line)
                    spec_line.append(match.groups()[0])
                specs.append(spec_line)

            description = json.dumps(specs)
        else:
            description = None

        reviews_endpoint = (
            "https://api.bazaarvoice.com/data/display/0.2alpha/product/summary?PassKey="
            "caLe64uePnBm2AJobXW3AWGdiTwA5fUMHMrBjNTAPTd8c&productid={}"
            "&contentType=reviews&rev=0&contentlocale=es*,es_CL".format(model_id)
        )
        reviews_json = session.get(reviews_endpoint).json()["reviewSummary"]
        review_count = reviews_json["numReviews"]
        review_avg_score = reviews_json["primaryRating"]["average"]

        return [
            Product(
                name[:250],
                cls.__name__,
                category,
                url,
                url,
                model_id,
                stock,
                price,
                price,
                cls.currency,
                sku=sku,
                picture_urls=picture_urls,
                part_number=sku,
                positions=positions,
                allow_zero_prices=not cls.skip_products_without_price,
                description=description,
                review_count=review_count,
                review_avg_score=review_avg_score,
            )
        ]

    @classmethod
    def _category_paths(cls):
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def preflight(cls, extra_args=None):
        session = session_with_proxy(extra_args)
        coveo_token_url = (
            "https://www.lg.com/{}/jcr:" "content.coveoToken.json"
        ).format(cls.region_code.lower())
        response = session.get(coveo_token_url)
        json_response = response.json()
        coveo_token = json_response["token"]
        return {"coveo_token": coveo_token}
