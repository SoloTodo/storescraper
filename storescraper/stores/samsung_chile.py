from collections import defaultdict
from decimal import Decimal

from storescraper.categories import (
    NOTEBOOK,
    CELL,
    TABLET,
    WEARABLE,
    HEADPHONES,
    CELL_ACCESORY,
    TELEVISION,
    STEREO_SYSTEM,
    REFRIGERATOR,
    WASHING_MACHINE,
    OVEN,
    DISH_WASHER,
    VACUUM_CLEANER,
    AIR_CONDITIONER,
    MONITOR,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy

import json


class SamsungChile(Store):
    url_extensions = [
        ("01010000", CELL, "Smartphones"),
        ("01020000", TABLET, "Tablets"),
        ("01030000", WEARABLE, "Smartwatches"),
        ("01040000", HEADPHONES, "Galaxy Buds"),
        ("01050000", CELL_ACCESORY, "Accesorios"),
        ("04010000", TELEVISION, "TVs"),
        ("05010000", STEREO_SYSTEM, "Equipos de Audio"),
        ("08030000", REFRIGERATOR, "Refrigeradores"),
        ("08010000", WASHING_MACHINE, "Lavadoras / Secadoras"),
        ("08080000", OVEN, "Cocina"),
        ("08090000", DISH_WASHER, "Lavavajillas"),
        ("08070000", VACUUM_CLEANER, "Aspiradoras"),
        ("08050000", AIR_CONDITIONER, "Soluciones de Aire"),
        ("07010000", MONITOR, "Monitores"),
        ("03010000", NOTEBOOK, "Galaxy Book"),
    ]

    @classmethod
    def categories(cls):
        return list({x[1] for x in cls.url_extensions})

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        page_size = 100
        api_url = (
            "https://searchapi.samsung.com/v6/front/b2c/product/"
            "finder/newhybris?siteCode=cl&num={}"
            "&onlyFilterInfoYN=N".format(page_size)
        )

        product_entries = defaultdict(lambda: [])

        for category_id, category_name, section_name in cls.url_extensions:
            if category_name != category:
                continue

            offset = 0
            current_position = 1
            while True:
                if offset > page_size * 10:
                    raise Exception("Page overflow")

                category_endpoint = api_url + "&type={}&start={}".format(
                    category_id, offset
                )
                print(category_endpoint)

                response = session.get(category_endpoint)
                json_data = json.loads(response.text)["response"]
                product_lists = json_data["resultData"]["productList"]

                if not product_lists:
                    break

                for product_list in product_lists:
                    for model in product_list["modelList"]:
                        product_url = (
                            "https://www.samsung.com"
                            + model["pdpUrl"]
                            + "?model="
                            + model["modelCode"]
                        )
                        product_entries[product_url].append(
                            {
                                "category_weight": 1,
                                "section_name": section_name,
                                "value": current_position,
                            }
                        )
                    current_position += 1

                offset += page_size

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        model = url.split("?model=")[1]
        endpoint = (
            "https://searchapi.samsung.com/v6/front/b2c/product/card/detail/newhybris?"
            "modelList={}&siteCode=cl&saleSkuYN=N&onlyRequestSkuYN=Y&commonCodeYN=N"
        ).format(model)

        response = session.get(endpoint)
        json_data = json.loads(response.text)["response"]["resultData"]

        products = []

        for product in json_data["productList"]:
            for model in product["modelList"]:
                # print(json.dumps(model))
                if model["reviewCount"]:
                    review_count = int(model["reviewCount"])
                    review_avg_score = float(model["ratings"])
                else:
                    review_count = 0
                    review_avg_score = None

                name = model["displayName"]
                variant_specs = []

                for spec_entry in model["fmyChipList"]:
                    variant_specs.append(spec_entry["fmyChipName"].strip())

                if variant_specs:
                    name += " ({})".format(" / ".join(variant_specs))

                if "www.samsung.com" in model["pdpUrl"]:
                    model_url = "https:{}".format(model["pdpUrl"])
                else:
                    model_url = "https://www.samsung.com{}".format(model["pdpUrl"])
                key = model["modelCode"]
                picture_urls = ["https:" + model["thumbUrl"]]

                for picture in model["galleryImage"] or []:
                    picture_urls.append("https:" + picture)

                if model["promotionPrice"]:
                    price = Decimal(model["promotionPrice"])
                elif model["priceDisplay"]:
                    price = Decimal(model["priceDisplay"])
                else:
                    price = Decimal(0)
                price = price.quantize(0)

                if model["stockStatusText"] == "inStock":
                    stock = -1
                else:
                    stock = 0

                products.append(
                    Product(
                        "{} ({})".format(name, key),
                        cls.__name__,
                        category,
                        model_url,
                        url,
                        key,
                        stock,
                        price,
                        price,
                        "CLP",
                        sku=key,
                        picture_urls=picture_urls,
                        allow_zero_prices=True,
                        review_count=review_count,
                        review_avg_score=review_avg_score,
                        part_number=key,
                    )
                )
        return products
