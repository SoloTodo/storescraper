import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy
from storescraper.categories import (
    KEYBOARD,
    HEADPHONES,
    STEREO_SYSTEM,
    EXTERNAL_STORAGE_DRIVE,
    TABLET,
    WEARABLE,
)


class NewHorizons(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos", HEADPHONES],
        ["parlantes", STEREO_SYSTEM],
        ["computacion", EXTERNAL_STORAGE_DRIVE],
        ["teclado-y-mouse", KEYBOARD],
        ["tablets-y-telefonos", TABLET],
        ["wearables", WEARABLE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://nht.cl/collections/{}?page" "={}".format(
                url_extension, page
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html.parser")
            product_containers = soup.findAll("product-card")
            if not product_containers or len(product_containers) == 0:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a", "bold")["href"]
                product_urls.append("https://nht.cl" + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[0].text
        )

        key = str(json_data["productID"])
        name = json_data["name"]
        sku = json_data["sku"]
        description = json_data["description"]
        offer = json_data["offers"][0]
        price = Decimal(offer["price"])

        if offer["availability"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        picture_urls = []
        for i in soup.findAll("div", "product-gallery__media"):
            picture_urls.append("https:" + i.find("img")["src"])

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
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
