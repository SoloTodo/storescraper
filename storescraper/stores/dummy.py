import json
import requests
from decimal import Decimal
from storescraper.categories import (
    PRINTER,
    OVEN,
    MICROPHONE,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    KEYBOARD,
    PROCESSOR,
    CELL,
    STOVE,
    GROCERIES,
    RAM,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy
import time


class Dummy(StoreWithUrlExtensions):
    url_extensions = [
        ["dummy-printer", PRINTER],
        ["dummy-oven", OVEN],
        ["dummy-microphone", MICROPHONE],
        ["dummy-monitor", MONITOR],
        ["dummy-motherboard", MOTHERBOARD],
        ["dummy-mouse", MOUSE],
        ["dummy-keyboard", KEYBOARD],
        ["dummy-processor", PROCESSOR],
        ["dummy-cell", CELL],
        ["dummy-stove", STOVE],
        ["dummy-groceries", GROCERIES],
        ["dummy-ram", RAM],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        print(url_extension)
        time.sleep(1)

        data = json.loads(
            requests.get(f"http://localhost:9871/{url_extension}.json").text
        )
        product_urls = []

        if len(set(data["urls"])) != len(data["urls"]):
            exit()

        for url in data["urls"]:
            product_urls.append(url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)

        data = json.loads(
            requests.get(f"http://localhost:9871/dummy-{category.lower()}.json").text
        )

        for link in data["urls"]:
            if url == link:
                return [
                    Product(
                        f"Dummy {category} {url}",
                        cls.__name__,
                        category,
                        url,
                        url,
                        "123",
                        -1,
                        Decimal("100000"),
                        Decimal("90000"),
                        "CLP",
                    )
                ]

        return []
