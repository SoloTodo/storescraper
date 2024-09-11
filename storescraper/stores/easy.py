import base64
import json
from collections import defaultdict
from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import (
    AIR_CONDITIONER,
    OVEN,
    REFRIGERATOR,
    SPACE_HEATER,
    VACUUM_CLEANER,
    WASHING_MACHINE,
    VIDEO_GAME_CONSOLE,
    WATER_HEATER,
    STOVE,
)

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, vtex_preflight


class Easy(Store):
    @classmethod
    def categories(cls):
        return [
            REFRIGERATOR,
            OVEN,
            VACUUM_CLEANER,
            WASHING_MACHINE,
            AIR_CONDITIONER,
            SPACE_HEATER,
            VIDEO_GAME_CONSOLE,
            WATER_HEATER,
            STOVE,
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            # Electrohogar y climatización
            # Calefacción
            [
                "electrohogar-y-climatizacion/calefaccion/estufas-electricas",
                [SPACE_HEATER],
                "Inicio > Electrohogar > Calefacción > Estufas Eléctricas",
                1,
            ],
            [
                "electrohogar-y-climatizacion/calefaccion/estufas-a-pellet",
                [SPACE_HEATER],
                "Inicio > Electrohogar > Calefacción > Estufas a Pellet",
                1,
            ],
            [
                "electrohogar-y-climatizacion/calefaccion/estufas-a-gas",
                [SPACE_HEATER],
                "Inicio > Electrohogar > Calefacción > Estufas a Gas",
                1,
            ],
            [
                "electrohogar-y-climatizacion/calefaccion/estufas-a-parafina",
                [SPACE_HEATER],
                "Inicio > Electrohogar > Calefacción > Estufas a Parafina",
                1,
            ],
            [
                "electrohogar-y-climatizacion/calefaccion/estufas-a-lena",
                [SPACE_HEATER],
                "Inicio > Electrohogar > Calefacción > Estufas a leña",
                1,
            ],
            # Refrigeración
            [
                "electrohogar-y-climatizacion/refrigeracion/refrigeradores",
                [REFRIGERATOR],
                "Inicio > Electrohogar y Climatización > Refrigeración > "
                "Refrigeradores",
                1,
            ],
            [
                "electrohogar-y-climatizacion/refrigeracion/freezer",
                [REFRIGERATOR],
                "Inicio > Electrohogar y Climatización > Refrigeración > " "Freezer",
                1,
            ],
            [
                "electrohogar-y-climatizacion/refrigeracion/frigobar",
                [REFRIGERATOR],
                "Inicio > Electrohogar y Climatización > Refrigeración > " "Frigobar",
                1,
            ],
            # Cocina
            [
                "electrohogar-y-climatizacion/cocina/hornos-empotrables",
                [OVEN],
                "Inicio > Electrohogar y Climatización > Cocina > "
                "Hornos Empotrables",
                1,
            ],
            [
                "electrohogar-y-climatizacion/electrodomesticos/microondas",
                [OVEN],
                "Inicio > Electrohogar y Climatización > Cocina > Microondas",
                1,
            ],
            # Lavado y planchado
            [
                "electrohogar-y-climatizacion/lavado-y-planchado/lavadoras",
                [WASHING_MACHINE],
                "Inicio > Electrohogar y Climatización > Lavado y planchado > "
                "Lavadoras",
                1,
            ],
            [
                "electrohogar-y-climatizacion/lavado-y-planchado/secadoras",
                [WASHING_MACHINE],
                "Inicio > Electrohogar y Climatización > Lavado y planchado > "
                "Secadoras",
                1,
            ],
            [
                "electrohogar-y-climatizacion/lavado-y-planchado/lavadoras-"
                "secadoras",
                [WASHING_MACHINE],
                "Inicio > Electrohogar y Climatización > Lavado y planchado > "
                "Lava - seca",
                1,
            ],
            # Aspirado y limpieza
            [
                "electrohogar-y-climatizacion/aspirado-y-limpieza/aspiradoras",
                [VACUUM_CLEANER],
                "Inicio > Electrohogar y Climatización > Aspirado y limpieza > "
                "Aspiradoras",
                1,
            ],
            [
                "electrohogar-y-climatizacion/aspirado-y-limpieza/robots-de-"
                "limpieza",
                [VACUUM_CLEANER],
                "Inicio > Electrohogar y Climatización > Aspirado y limpieza > "
                "Robots de limpieza",
                1,
            ],
            # Electrodomésticos
            [
                "electrohogar-y-climatizacion/electrodomesticos/hornos-" "electricos",
                [OVEN],
                "Inicio > Electrohogar y Climatización > Electrodomésticos > "
                "Hornos eléctricos",
                1,
            ],
            [
                "electrohogar-y-climatizacion/electrodomesticos/microondas",
                [OVEN],
                "Inicio > Electrohogar y Climatización > Electrodomésticos > "
                "Microondas",
                1,
            ],
            # Ventilación
            [
                "electrohogar-y-climatizacion/ventilacion/aire-acondicionado-"
                "portatil",
                [AIR_CONDITIONER],
                "Inicio > Electrohogar y Climatización > Ventilación > "
                "Aire acondicionado portátil",
                1,
            ],
            [
                "electrohogar-y-climatizacion/ventilacion/aire-acondicionado-" "split",
                [AIR_CONDITIONER],
                "Inicio > Electrohogar y Climatización > Ventilación > "
                "Aire Acondicionado split",
                1,
            ],
            [
                "electrohogar-y-climatizacion/ventilacion/purificadores-y-"
                "humidificadores",
                [AIR_CONDITIONER],
                "Inicio > Electrohogar y Climatización > Ventilación > "
                "Purificadores y humidificadores",
                1,
            ],
            [
                "electrohogar-y-climatizacion/calefont-y-termos/calefont",
                [WATER_HEATER],
                "Inicio > Electrohogar y Climatización > Calefont y Termos > "
                "Calefont",
                1,
            ],
            [
                "electrohogar-y-climatizacion/tecnologia/consolas-y-"
                "videojuegos/consolas",
                [VIDEO_GAME_CONSOLE],
                "Electrohogar y Climatización > Tecnología > "
                "Consolas y Videojuegos > Consolas",
                1,
            ],
            [
                "electrohogar-y-climatizacion/cocina/cocinas-a-gas",
                [STOVE],
                "Electrohogar y Climatización > Cocina > Cocina a gas",
                1,
            ],
            [
                "electrohogar-y-climatizacion/cocina/encimeras",
                [STOVE],
                "Electrohogar y Climatización > Cocina > Encimeras",
                1,
            ],
        ]

        product_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 1

            while True:
                if page > 20:
                    raise Exception("page overflow: " + category_path)

                url = f"https://cl-ccom-easy-bff-web.ecomm.cencosud.com/v2/search/categories?count=40&page={page}&categories={category_path}"

                response = session.get(
                    url, headers={"X-Api-Key": "jFt3XhoLqFAGr6qN9SCpr9K6y83HpakP"}
                ).json()

                if response["productList"] == []:
                    break

                for idx, product in enumerate(response["productList"]):
                    product_entries[
                        f"https://www.easy.cl/{product['linkText']}"
                    ].append(
                        {
                            "category_weight": category_weight,
                            "section_name": section_name,
                            "value": idx + 1,
                        }
                    )

                page += 1

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["Content-Type"] = "application/json"
        product_urls = []

        base_prod_url = "https://www.easy.cl/tienda/producto/{}"
        prods_url = "https://www.easy.cl/api//prodeasy/_search"

        prods_data = {
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "bool": {
                                        "should": [
                                            {
                                                "function_score": {
                                                    "query": {
                                                        "multi_match": {
                                                            "query": keyword,
                                                            "fields": [
                                                                "name^1000",
                                                                "brand",
                                                                "cat_3.stop",
                                                                "partNumber",
                                                            ],
                                                            "type": "best_fields",
                                                            "operator": "and",
                                                        }
                                                    },
                                                    "field_value_factor": {
                                                        "field": "boost",
                                                        "factor": 6,
                                                    },
                                                }
                                            },
                                            {
                                                "multi_match": {
                                                    "query": keyword,
                                                    "fields": ["name^8", "cat_3.stop"],
                                                    "type": "best_fields",
                                                    "operator": "or",
                                                }
                                            },
                                            {
                                                "span_first": {
                                                    "match": {
                                                        "span_term": {
                                                            "name.dym": keyword
                                                        }
                                                    },
                                                    "end": 1,
                                                    "boost": 2000,
                                                }
                                            },
                                        ],
                                        "minimum_should_match": "1",
                                    }
                                }
                            ]
                        }
                    },
                    "boost_mode": "sum",
                    "score_mode": "max",
                }
            },
            "size": 450,
            "from": 0,
        }

        prods_response = session.post(prods_url, data=json.dumps(prods_data))

        prods_json = json.loads(prods_response.text)
        prods_hits = prods_json["hits"]["hits"]

        if not prods_hits:
            return []

        for prods_hit in prods_hits:
            product_url = base_prod_url.format(prods_hit["_source"]["url"])
            product_urls.append(product_url)

            if len(product_urls) == threshold:
                return product_urls

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        sku = url.split("-")[-1]
        response = session.get(
            f"https://cl-ccom-easy-bff-web.ecomm.cencosud.com/v2/products/by-sku/{sku}",
            headers={"X-Api-Key": "jFt3XhoLqFAGr6qN9SCpr9K6y83HpakP"},
        ).json()
        assert len(response["items"]) == 1

        item = response["items"][0]
        name = response["productName"]
        key = response["productId"]
        picture_urls = [img["imageUrl"] for img in item["images"]]

        for seller in item["sellers"]:
            if seller["sellerName"] == "Easy.cl":
                offer = seller["commertialOffer"]
                normal_price = Decimal(offer["prices"]["normalPrice"])

                if "offerPrice" in offer["prices"] and offer["prices"]["offerPrice"]:
                    offer_price = Decimal(offer["prices"]["offerPrice"])
                else:
                    offer_price = normal_price

                stock = offer["availableQuantity"]
                break

        description = html_to_markdown(response["description"])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            "CLP",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
