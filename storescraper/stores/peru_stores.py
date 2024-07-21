from decimal import Decimal
import logging
import random
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13, html_to_markdown, session_with_proxy


class PeruStores(Store):
    base_url = ""
    params = ""
    product_container_class = ""

    categories_json = {}
    international_produt_code = ""
    seller_id = "1"
    currency = "PEN"
    sku_is_item_id = True

    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        if category != TELEVISION:
            return []
        page = 1
        while True:
            if page > 30:
                raise Exception("Page overflow")

            url_webpage = "{}/buscapagina?{}&PageNumber={}".format(
                cls.base_url, cls.params, page
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")

            product_containers = soup.findAll("div", cls.product_container_class)
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category")
                break
            for container in product_containers:
                product_urls.append(container.find("a")["href"])
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        key_input = soup.find("input", {"id": "___rc-p-id"})
        if not key_input:
            return []

        key = key_input["value"]
        product_info = session.get(
            "{}/api/catalog_"
            "system/pub/products/search/"
            "?fq=productId:{}&v={}".format(cls.base_url, key, random.randint(0, 1000))
        ).json()[0]
        category_path = product_info["categories"][0].split("/")[-2].lower()
        category = cls.categories_json.get(category_path, category)
        name = product_info["productName"]

        item_data = product_info["items"][0]
        if cls.sku_is_item_id:
            sku = item_data["itemId"]
        else:
            sku = product_info["productReference"]

        for seller in item_data["sellers"]:
            if seller["sellerId"] == cls.seller_id:
                store_seller = seller
                break
        else:
            return []

        if cls.international_produt_code in product_info["productClusters"]:
            # Producto internacional
            stock = 0
        else:
            stock = store_seller["commertialOffer"]["AvailableQuantity"]

        normal_price = Decimal(str(store_seller["commertialOffer"]["Price"]))

        # Price will be zero if the product is not sold directly by retailer
        if not normal_price:
            return []

        offer_price = cls.get_offer_price(session, sku, normal_price, store_seller)

        picture_urls = [x["imageUrl"].split("?")[0] for x in item_data["images"]]

        if check_ean13(item_data["ean"]):
            ean = item_data["ean"]
        else:
            ean = None

        description = product_info.get("description", None)
        if description:
            description = html_to_markdown(description)

        part_number = product_info.get("Modelo", None)
        if part_number:
            part_number = part_number[0]

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
            cls.currency,
            sku=sku,
            picture_urls=picture_urls,
            ean=ean,
            description=description,
            part_number=part_number,
        )
        return [p]

    @classmethod
    def get_offer_price(cls, session, sku, normal_price, store_seller):
        return normal_price
