import base64
import urllib
from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION, STEREO_SYSTEM, HEADPHONES
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, check_ean13, vtex_preflight


class Philips(StoreWithUrlExtensions):
    url_extensions = [
        ["imagen-y-sonido/televisores", TELEVISION],
        ["imagen-y-sonido/audio/audifonos", HEADPHONES],
        ["imagen-y-sonido/audio/barras-de-sonido", STEREO_SYSTEM],
        ["imagen-y-sonido/audio/parlantes-inalambricos", STEREO_SYSTEM],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 0
        step = 12
        facet_name = url_extension.split("/")[-1]
        while True:
            if page > step * 10:
                raise Exception("Page overflow: " + url_extension)

            variables_dict = {
                "hideUnavailableItems": False,
                "skusFilter": "ALL_AVAILABLE",
                "simulationBehavior": "default",
                "installmentCriteria": "MAX_WITHOUT_INTEREST",
                "productOriginVtex": True,
                "map": "c,c",
                "query": url_extension,
                "orderBy": "OrderByPriceASC",
                "from": page * step,
                "to": (page + 1) * step - 1,
                "selectedFacets": [{"key": "c", "value": facet_name}],
                "facetsBehavior": "Static",
                "categoryTreeBehavior": "default",
                "withFacets": False,
            }

            query_extensions = {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": extra_args["sha256Hash"],
                    "sender": "vtex.store-resources@0.x",
                    "provider": "vtex.search-graphql@0.x",
                },
                "variables": base64.b64encode(
                    json.dumps(variables_dict).encode("utf-8")
                ).decode("utf-8"),
            }

            endpoint = (
                "https://www.tienda.philips.cl/_v/segment/"
                "graphql/v1?extensions={}".format(
                    urllib.parse.quote(json.dumps(query_extensions))
                )
            )
            response = session.get(endpoint)
            json_data = json.loads(response.text)

            product_containers = json_data["data"]["productSearch"]["products"]
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = "https://www.tienda.philips.cl/{}/p".format(
                    container["linkText"]
                )
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        soup = BeautifulSoup(res.text, "lxml")
        state_tag = soup.find("template", {"data-varname": "__STATE__"})
        product_data = json.loads(state_tag.find("script").text)

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        key = product_specs["productId"]
        name = product_specs["productName"]
        sku = product_specs["productReference"]
        description = product_specs.get("description", None)

        pricing_key = "${}.items.0.sellers.0.commertialOffer".format(base_json_key)
        pricing_data = product_data[pricing_key]

        price = Decimal(str(pricing_data["Price"]))
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
            "CLP",
            sku=sku,
            ean=ean,
            description=description,
            picture_urls=picture_urls,
        )
        return [p]

    @classmethod
    def preflight(cls, extra_args=None):
        return vtex_preflight(
            extra_args, "https://www.tienda.philips.cl/" "imagen-y-sonido/televisores"
        )
