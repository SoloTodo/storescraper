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
    PROJECTOR,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy

import json


class SamsungChile(Store):
    url_extensions = [
        ("01010000", CELL, "Smartphones", []),
        ("01020000", TABLET, "Tablets", []),
        ("01030000", WEARABLE, "Smartwatches", []),
        ("01040000", HEADPHONES, "Galaxy Buds", []),
        ("01050000", CELL_ACCESORY, "Accesorios", []),
        (
            "04010000",
            TELEVISION,
            "TVs",
            [
                ("filter2=05z01", "Neo QLED"),
                ("filter2=05z02", "QLED"),
                ("filter2=05z09", "OLED"),
                ("filter1=05z01", "The Frame"),
                ("filter1=05z02", "The Serif"),
                ("filter1=05z04", "The Terrace"),
                ("filter1=05z03", "The Sero"),
                ("filter2=05z03", "Crystal UHD"),
                ("filter3=03o06", '32" pulgadas'),
                ("filter3=03o05", '43" pulgadas'),
                ("filter3=03o04", '50" pulgadas'),
                ("filter3=03o03", '55" pulgadas'),
                ("filter3=03o02", '65" pulgadas'),
                ("filter3=03o01", '75" pulgadas'),
                ("filter3=03o07", '85" pulgadas'),
                ("filter3=03o08", '98" pulgadas'),
                ("filter4=02z05", "8K TVs"),
                ("filter4=02z01", "4K TVs"),
            ],
        ),
        (
            "05010000",
            STEREO_SYSTEM,
            "Equipos de Audio",
            [
                ("filter1=03i01&filter2=02z05", "Soundbars Serie Q"),
                ("filter1=03i01&filter2=02z04", "Soundbars Serie S"),
                ("filter1=03i01&filter2=02z01", "Soundbars"),
                ("filter1=03i02", "Sound Towers"),
            ],
        ),
        (
            "08030000",
            REFRIGERATOR,
            "Refrigeradores",
            [
                ("filter7=04z09", "Family Hub"),
                ("filter2=05z01", "BESPOKE"),
                ("filter3=01i03", "French Door"),
                ("filter3=01i01", "Side by Side"),
                ("filter3=01i02", "Bottom Mount Freezer"),
                ("filter3=01i09", "1 Door Flex"),
                ("filter3=01i04", "Top Mount Freezer"),
            ],
        ),
        (
            "08010000",
            WASHING_MACHINE,
            "Lavadoras / Secadoras",
            [
                ("filter2=05z05", "Carga Frontal"),
                ("filter2=05z01", "Carga Superior"),
                ("filter2=05z04", "Secadoras"),
                ("filter2=05z07", "Apilables"),
            ],
        ),
        (
            "08080000",
            OVEN,
            "Cocina",
            [
                ("filter2=03z01", "Hornos Bespoke"),
                ("filter2=03z03", "Encimeras"),
                ("filter2=03z02", "Cocinas a Gas"),
                ("filter2=03z04", "Campanas"),
                ("filter1=01i01", "Todo Microondas"),
            ],
        ),
        ("08090000", DISH_WASHER, "Lavavajillas", []),
        (
            "08070000",
            VACUUM_CLEANER,
            "Aspiradoras",
            [
                ("filter2=01i02", "Stick"),
                ("filter2=01i03", "Robot"),
                ("filter2=01i01", "Arrastre"),
            ],
        ),
        (
            "08050000",
            AIR_CONDITIONER,
            "Soluciones de Aire",
            [
                ("filter1=03z01", "A/C Split"),
                ("filter1=03z02", "A/C MultiSplit"),
                ("filter1=03z03", "A/C Split Cassette 360"),
                ("filter1=03z01", "Purificadores de Aire"),
            ],
        ),
        (
            "07010000",
            MONITOR,
            "Monitores",
            [
                ("filter1=01i03", "Gamer"),
                ("filter1=01i08", "Monitores Smart"),
                ("filter1=01i02", "High Resolution"),
                ("filter1=01i01", "Curvo"),
            ],
        ),
        (
            "03010000",
            NOTEBOOK,
            "Galaxy Book",
            [
                ("filter3=02z05", "Galaxy Book3 Ultra"),
                ("filter3=02z06", "Galaxy Book3 Pro 360"),
                ("filter3=02z07", "Galaxy Book3 Pro"),
                ("filter3=02z08", "Galaxy Book3 360"),
                ("filter3=02z09", "Galaxy Book3"),
            ],
        ),
        (
            "04050000",
            PROJECTOR,
            "Proyectores",
            [("filter1=01i01", "The Premier"), ("filter1=01i02", "The Freestyle")],
        ),
    ]

    @classmethod
    def categories(cls):
        return list({x[1] for x in cls.url_extensions})

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        product_entries = defaultdict(lambda: [])

        for category_id, category_name, section_name, subsections in cls.url_extensions:
            if category_name != category:
                continue

            main_query = "type={}".format(category_id)
            main_section_data = cls.__discover_entries_for_query(
                main_query, section_name, extra_args
            )
            for product_url, entries in main_section_data.items():
                product_entries[product_url].extend(entries)

            for subsection_query, subsection_name in subsections:
                subsection_query = "{}&{}".format(main_query, subsection_query)
                subsection_data = cls.__discover_entries_for_query(
                    subsection_query, subsection_name, extra_args
                )
                for product_url, entries in subsection_data.items():
                    product_entries[product_url].extend(entries)

        return product_entries

    @classmethod
    def __discover_entries_for_query(cls, query, section_name, extra_args=None):
        session = session_with_proxy(extra_args)
        page_size = 100
        api_url = (
            "https://searchapi.samsung.com/v6/front/b2c/product/"
            "finder/newhybris?siteCode=cl&sort=recommended&num={}"
            "&onlyFilterInfoYN=N".format(page_size)
        )

        product_entries = defaultdict(lambda: [])
        offset = 0
        current_position = 1
        while True:
            if offset > page_size * 10:
                raise Exception("Page overflow")

            category_endpoint = api_url + "&{}&start={}".format(query, offset)
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
