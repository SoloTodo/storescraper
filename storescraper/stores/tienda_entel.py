import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TiendaEntel(Store):
    @classmethod
    def categories(cls):
        return [
            "Cell",
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        from .entel import Entel

        return Entel.discover_entries_for_category(category, extra_args)

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        return cls._products_for_url(url, extra_args)

    @classmethod
    def _products_for_url(cls, url, extra_args=None, retries=5):
        print(url)
        session = session_with_proxy(extra_args)

        products = []

        soup = BeautifulSoup(session.get(url).text, "lxml")
        product_detail_container = soup.find("div", {"id": "productDetail"})

        if not product_detail_container:
            # For the case of https://miportal.entel.cl/personas/producto/
            # prod1410051 that displays a blank page
            return []
        raw_json = product_detail_container.find("script").string

        if not raw_json:
            if retries:
                return cls._products_for_url(url, extra_args, retries=retries - 1)
            else:
                raise Exception("JSON error")

        try:
            json_data = json.loads(raw_json)
        except json.decoder.JSONDecodeError:
            return []

        if json_data["planPriceRange"]:
            offer_price = min(
                [x["priceIVA"] for x in json_data["planPriceRange"]["rangeDetail"]]
            )
            offer_price = Decimal(offer_price).quantize(0)
        else:
            offer_price = None

        base_name = json_data["renderVOBean"]["productName"]

        for sku in json_data["renderSkusBean"]["skus"]:
            if not sku["available"]:
                continue
            price_container = sku["skuPrice"]
            if not price_container:
                continue

            normal_price = Decimal(price_container).quantize(0)
            if not offer_price:
                offer_price = normal_price
            sku_id = sku["skuId"]

            pictures_container = []
            stock = 0

            for view in json_data["skuViews"]:
                if view["skuId"] == sku_id:
                    if view["visibilityButtonPdp"] != 0:
                        stock = view["stockDelivery"] + view["stockPickup"]
                    pictures_container = view["images"]
                    break

            picture_urls = []

            for container in pictures_container:
                picture_url = "https://miportal.entel.cl" + container["heroImage"]
                picture_urls.append(picture_url.replace(" ", "%20"))

            if "semi" in sku["skuName"].lower() or "semi" in base_name.lower():
                condition = "https://schema.org/RefurbishedCondition"
            else:
                condition = "https://schema.org/NewCondition"

            product = Product(
                sku["skuName"],
                cls.__name__,
                "Cell",
                url,
                url,
                sku_id,
                stock,
                normal_price,
                offer_price,
                "CLP",
                sku=sku_id,
                picture_urls=picture_urls,
                condition=condition,
            )
            products.append(product)

        return products
