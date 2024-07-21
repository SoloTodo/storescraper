import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13


class Geant(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [TELEVISION]
        session = session_with_proxy(extra_args)
        product_urls = []
        page_size = 30
        for local_category in url_extensions:
            if local_category != category:
                continue

            page = 0
            while True:
                if page > 10:
                    raise Exception("Page overflow")
                url_webpage = (
                    "https://www.geant.com.uy/api/catalog_system/"
                    "pub/products/search/busca?O=OrderByScoreDESC"
                    "&_from={}&_to={}&fq=B:56&ft=LG".format(
                        page * page_size, (page + 1) * page_size - 1
                    )
                )
                data = session.get(url_webpage)
                product_containers = data.json()
                if not product_containers:
                    break
                for container in product_containers:
                    product_url = container["linkText"]
                    product_urls.append(
                        "https://www.geant.com.uy/" + product_url + "/p"
                    )

                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        product_data_tag = soup.find("template", {"data-varname": "__STATE__"})
        product_data = json.loads(str(product_data_tag.find("script").contents[0]))

        if not product_data:
            return []

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        key = product_specs["productId"]
        name = product_specs["productName"]
        sku = product_specs["productReference"]
        description = product_specs.get("description", None)

        pricing_key = "${}.items.0.sellers.0.commertialOffer".format(base_json_key)
        pricing_data = product_data[pricing_key]

        exchange_rate = extra_args["exchange_rate"]
        price = Decimal(str(pricing_data["Price"] / exchange_rate)).quantize(
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

        ean = None
        for prop in product_specs["properties"]:
            if product_data[prop["id"]]["name"] == "EAN":
                ean = product_data[prop["id"]]["values"]["json"][0]
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
            "USD",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            ean=ean,
        )
        return [p]

    @classmethod
    def preflight(cls, extra_args=None):
        session = session_with_proxy(extra_args)
        res = session.get(
            "https://www.geant.com.uy/api/dataentities/DO/"
            "search?_sort=date%20DESC&_fields=exchange"
        )
        json_data = res.json()
        exchange_rate = json_data[0]["exchange"]
        return {"exchange_rate": exchange_rate}
