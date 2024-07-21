from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    CASE_FAN,
    COMPUTER_CASE,
    MOTHERBOARD,
    POWER_SUPPLY,
    PROCESSOR,
    RAM,
    SOLID_STATE_DRIVE,
    VIDEO_CARD,
    NOTEBOOK,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class MiningStore(StoreWithUrlExtensions):
    url_extensions = [
        ["almacenamiento", SOLID_STATE_DRIVE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["memoria-ram", RAM],
        ["placas-madre", MOTHERBOARD],
        ["tarjetas-de-video", VIDEO_CARD],
        ["accesorios", CASE_FAN],
        ["procesadores", PROCESSOR],
        ["notebooks", NOTEBOOK],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = (
                "https://www.miningstore.cl/product-category/"
                "{}/page/{}/".format(url_extension, page)
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("div", "product")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a", "product-image-link")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )

        for entry in json_data["@graph"]:
            if entry["@type"] == "Product":
                product_data = entry
                break
        else:
            raise Exception("No JSON product data found")

        name = product_data["name"]
        sku = str(product_data["sku"])
        description = str(product_data["description"])
        price = Decimal(product_data["offers"][0]["price"])

        if soup.find("p", "stock out-of-stock"):
            stock = 0
        elif soup.find("p", "stock in-stock"):
            stock = int(soup.find("p", "stock in-stock").text.split()[0])
        else:
            stock = -1

        picture_tags = soup.findAll("img", "wp-post-image")
        picture_urls = []

        for picture_tag in picture_tags:
            if "data-large_image" in picture_tag.attrs:
                picture_url = picture_tag["data-large_image"]
            else:
                picture_url = picture_tag["src"]
            picture_urls.append(picture_url)

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
            description=description,
            picture_urls=picture_urls,
        )
        return [p]
