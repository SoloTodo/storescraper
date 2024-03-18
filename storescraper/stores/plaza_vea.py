from decimal import Decimal
import logging

from storescraper.categories import (
    AIR_CONDITIONER,
    ALL_IN_ONE,
    CELL,
    HEADPHONES,
    NOTEBOOK,
    OVEN,
    REFRIGERATOR,
    STEREO_SYSTEM,
    TELEVISION,
    WASHING_MACHINE,
)
from storescraper.stores.peru_stores import PeruStores
from storescraper.utils import session_with_proxy


class PlazaVea(PeruStores):
    base_url = "https://www.plazavea.com.pe"

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []
        page_size = 50
        page = 0
        while True:
            if page > 15:
                raise Exception("Page overflow")
            url_webpage = (
                "https://www.plazavea.com.pe/api/io/_v/public/"
                "graphql/v1?workspace=master"
            )
            payload = {
                "query": "query productSearch($fullText: String, $selected"
                "Facets: [SelectedFacetInput], $from: Int, $to: Int, $orde"
                "rBy: String) {\n    productSearch(fullText: $fullText, se"
                "lectedFacets: $selectedFacets, from: $from, to: $to, orde"
                "rBy: $orderBy, hideUnavailableItems: true, productOriginV"
                'tex:true) @context(provider: "vtex.search-graphql") {\n'
                "      products {\n        cacheId\n        productId\n   "
                "     categoryId\n        description\n        productName"
                "\n        properties {\n          name\n          values"
                "\n        }\n        categoryTree{\n          id\n       "
                "   name\n          href\n          hasChildren\n         "
                " children {\n            id\n            name\n          "
                "  href\n          }\n        }\n        linkText\n       "
                " brand\n        link\n        clusterHighlights {\n      "
                "    id\n          name\n        }\n        skuSpecificati"
                "ons {\n          field {\n            name\n          }\n"
                "          values {\n            name\n          }\n      "
                "  }\n        items {\n          itemId\n          name\n "
                "         nameComplete\n          complementName\n        "
                "  ean\n          referenceId {\n            Key\n        "
                "    Value\n          }\n          measurementUnit\n      "
                "    unitMultiplier\n          images {\n            cache"
                "Id\n            imageId\n            imageLabel\n        "
                "    imageTag\n            imageUrl\n            imageText"
                "\n          }\n          sellers {\n            sellerId"
                "\n            sellerName\n            addToCartLink\n    "
                "        commertialOffer {\n              discountHighligh"
                "ts {\n                name\n              }\n            "
                "  Price\n              ListPrice\n              Tax\n    "
                "          taxPercentage\n              spotPrice\n       "
                "       PriceWithoutDiscount\n              RewardValue\n "
                "             PriceValidUntil\n              AvailableQuan"
                "tity\n              giftSkuIds\n              teasers {\n"
                "                name\n                conditions {\n     "
                "             minimumQuantity\n                  parameter"
                "s {\n                    name\n                    value"
                "\n                  }\n                }\n               "
                " effects {\n                  parameters {\n             "
                "       name\n                    value\n                 "
                " }\n                }\n              }\n            }\n  "
                "        }\n          variations{\n            name\n     "
                "       values\n          }\n        }\n        productClu"
                "sters{\n          id\n          name\n        }\n        "
                "itemMetadata {\n          items {\n            id\n      "
                "      assemblyOptions {\n              name\n            "
                "  required\n            }\n          }\n        }\n      "
                "}\n      redirect\n      recordsFiltered\n      operator"
                "\n      fuzzy\n      correction {\n        misspelled\n  "
                "    }\n    }\n  }",
                "variables": {
                    "fullText": "lg lg",
                    "selectedFacets": [{"key": "vendido-por", "value": "plazavea"}],
                    "from": page * page_size,
                    "to": (page + 1) * page_size - 1,
                    "orderBy": "OrderByScoreDESC",
                },
            }
            data = session.post(url_webpage, json=payload).json()
            product_containers = data["data"]["productSearch"]["products"]
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category")
                break
            for container in product_containers:
                link = "https://www.plazavea.com.pe/" + container["linkText"] + "/p"
                product_urls.append(link)
            page += 1
        return product_urls

    categories_json = {
        "parlantes": STEREO_SYSTEM,
        "soundbar": STEREO_SYSTEM,
        "equipos de sonido": STEREO_SYSTEM,
        "laptops": NOTEBOOK,
        "celulares y smartphones": CELL,
        "all in one": ALL_IN_ONE,
        "refrigeradoras": REFRIGERATOR,
        "lavadoras": WASHING_MACHINE,
        "lavaseca": WASHING_MACHINE,
        "secadoras": WASHING_MACHINE,
        "cocinas de pie": OVEN,
        "hornos microondas": OVEN,
        "aire acondicionado": AIR_CONDITIONER,
        "audífonos": HEADPHONES,
    }
    international_produt_code = "10178"

    @classmethod
    def get_offer_price(cls, session, sku, normal_price, store_seller):
        payload = {
            "items": [{"id": sku, "quantity": 1, "seller": "1"}],
            "country": "PER",
        }
        offer_info = session.post(
            "https://www.plazavea.com.pe/api/checkout/pu"
            "b/orderforms/simulation?sc=1",
            json=payload,
        ).json()
        if offer_info["ratesAndBenefitsData"]:
            teaser = offer_info["ratesAndBenefitsData"]["teaser"]
            if len(teaser) != 0:
                discount = teaser[0]["effects"]["parameters"][-1]["value"]

                list_price = Decimal(str(store_seller["commertialOffer"]["ListPrice"]))
                offer_price = (list_price - Decimal(discount)).quantize(0)
            else:
                offer_price = normal_price
        else:
            offer_price = normal_price

        if offer_price > normal_price:
            offer_price = normal_price

        return offer_price
