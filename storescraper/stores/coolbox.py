from decimal import Decimal
import json
import logging
import re
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Coolbox(Store):
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

        while True:
            if page > 25:
                raise Exception("Page overflow")

            url = "https://www.coolbox.pe/lg?page={}".format(page)
            print(url)

            res = session.get(url)
            product_containers = json.loads(
                "{" + re.search(r"__STATE__ = {(.+)}", res.text).groups()[0] + "}"
            )

            r = re.compile(r"Product:sp-(\d+$)")

            product_container_keys = product_containers.keys()
            products_to_find = list(filter(r.match, product_container_keys))
            if not products_to_find:
                if page == 1:
                    logging.warning("Empty category: " + category)
                break

            for product_key in products_to_find:
                product_url = product_containers[product_key]["link"]
                product_urls.append("https://www.coolbox.pe" + product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        product_match = re.search(r"__STATE__ = {(.+)}", response.text)
        if not product_match:
            return []

        product_data = json.loads("{" + product_match.groups()[0] + "}")
        base_json_keys = list(product_data.keys())

        if not base_json_keys:
            return []

        base_json_key = base_json_keys[0]
        product_specs = product_data[base_json_key]

        key_key = "{}.items.0".format(base_json_key)
        key = product_data[key_key]["itemId"]

        name = product_specs["productName"]
        sku = product_specs["productReference"]
        description = html_to_markdown(product_specs.get("description", None))

        seller_entry = None

        seller_idx = 0
        while True:
            seller_key = "{}.items.0.sellers.{}".format(base_json_key, seller_idx)
            if seller_key not in product_data:
                break
            if (
                product_data[seller_key]["sellerId"] == "1"
                and product_data[seller_key]["sellerDefault"]
            ):
                seller_entry_key = "${}.items.0.sellers.0.commertialOffer".format(
                    base_json_key, seller_key
                )
                seller_entry = product_data[seller_entry_key]
                break
            seller_idx += 1

        if not seller_entry:
            return []

        price = Decimal(str(seller_entry["Price"]))

        if not price:
            return []

        stock = seller_entry["AvailableQuantity"]

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
            "PEN",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
