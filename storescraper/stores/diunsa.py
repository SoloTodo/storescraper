import json


from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Diunsa(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only gets LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1

        done = False
        while not done:
            if page > 30:
                raise Exception("Page overflow")

            url = "https://www.diunsa.hn/lg%20lg?_q=lg%20lg&" "page={}".format(page)

            soup = BeautifulSoup(session.get(url).text, "lxml")
            page_state_tag = soup.find("template", {"data-varname": "__STATE__"})
            page_state = json.loads(page_state_tag.find("script").string)

            done = True
            for key, product in page_state.items():
                if "productId" not in product:
                    continue
                done = False
                product_url = "https://www.diunsa.hn/{}/p".format(product["linkText"])
                product_urls.append(product_url)

            if done and page == 1:
                raise Exception("Empty site")

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html5lib")

        product_data = json.loads(
            soup.find("template", {"data-varname": "__STATE__"}).find("script").string
        )

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        key_key = "{}.items.0".format(base_json_key)
        key = product_data[key_key]["itemId"]
        name = product_specs["productName"]
        sku = product_specs["productId"]
        part_number = product_specs["productReference"]
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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
