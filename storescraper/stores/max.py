import logging
import json

from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import (
    session_with_proxy,
    html_to_markdown,
    magento_picture_urls,
)
from storescraper.categories import TELEVISION


class Max(StoreWithUrlExtensions):
    url_extensions = [
        ["1964", TELEVISION],
    ]
    headers = {"x-api-key": "ROGi1LWB3saRqFw4Xdqc4Z9jGWVxYLl9ZEZjbJu9"}
    v1_api_base_url = "https://apigt.tienda.max.com.gt/v1"

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            if page >= 5:
                raise Exception("Page overflow")

            api_endpoint = f"https://apigt.tienda.max.com.gt/v2/products?categories={url_extension}&page={page}&pageSize=200&sessionId=1&clientId=e0a1625b-3c2b-4552-bce9-07d32ca12d59"
            print(api_endpoint)
            data = session.get(
                api_endpoint,
                headers=cls.headers,
            ).text
            json_data = json.loads(data)

            if json_data["products"] == []:
                if page == 1:
                    raise Exception("Empty category")

                break

            product_urls.extend(
                [
                    f"https://tienda.max.com.gt/{product['meta']['url_key']}"
                    for product in json_data["products"]
                ]
            )
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        product = json.loads(soup.find("script", {"id": "__NEXT_DATA__"}).text)[
            "props"
        ]["pageProps"]["product"]

        name = product["title"]
        picture_urls = [img["url"] for img in product["gallery"]]
        sku = product["sku"]

        prices = json.loads(
            session.get(
                f"{cls.v1_api_base_url}/prices/{sku}",
                headers=cls.headers,
            ).text
        )
        normal_price = Decimal(prices["regularPrice"]["value"])
        sales_price = prices["salesPrice"]
        normal_price = Decimal(sales_price["value"]) if sales_price else normal_price

        summary = json.loads(
            session.get(
                f"{cls.v1_api_base_url}/products/{sku}/contentSyndication",
                headers=cls.headers,
            ).text
        )
        description = ""

        if summary["dimensions"]:
            description += "Dimensiones:\n"

            for dimension in summary["dimensions"]:
                description += f"- {dimension['label']}: {dimension['value']}\n"

        description += "\nEspecificaciones:\n"

        for spec in summary["specs"]:
            description += f"- {spec['label']}: {spec['value']}\n"

        stock_info = json.loads(
            session.get(
                f"{cls.v1_api_base_url}/products/{sku}/stock",
                headers=cls.headers,
            ).text
        )

        stock = (
            0
            if stock_info["status"] == "OUT_OF_STOCK"
            else stock_info["salableQuantity"]
        )

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            normal_price,
            "GTQ",
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
