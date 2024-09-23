import json
import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    WEARABLE,
    KEYBOARD,
    HEADPHONES,
    ALL_IN_ONE,
    TABLET,
    CELL,
    NOTEBOOK,
    STEREO_SYSTEM,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class BackOnline(StoreWithUrlExtensions):
    url_extensions = [
        ("WATCH", WEARABLE),
        ("ACCESORIOS", KEYBOARD),
        ("AUDÍFONOS", HEADPHONES),
        ("IMAC", ALL_IN_ONE),
        ("IPAD", TABLET),
        ("IPHONE", CELL),
        ("MACBOOK", NOTEBOOK),
        ("OPEN BOX", NOTEBOOK),
        ("PARLANTES", STEREO_SYSTEM),
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []

        for collection_label, collection_url in extra_args["collection_urls"]:
            if url_extension not in collection_label:
                continue

            page = 1
            while True:
                if page >= 10:
                    raise Exception("Page overflow: " + url_extension)

                url_webpage = "{}?page={}".format(collection_url, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, "lxml")
                link_containers = soup.findAll("li", "grid__item")

                if not link_containers:
                    if page == 1:
                        logging.warning("Empty category: " + url_extension)
                    break

                for link_container in link_containers:
                    product_url = (
                        "https://backonline.cl" + link_container.find("a")["href"]
                    )
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, "lxml")

        json_tag = soup.findAll("script", {"type": "application/ld+json"})
        json_data = json.loads(json_tag[1].text)
        json_data_tags = [tag.lower() for tag in json_data["tags"]]
        variations_tags = soup.findAll("script", {"type": "application/json"})
        products = []
        product_caption = soup.find(
            "p", "product__text caption-with-letter-spacing"
        ).text.lower()

        if "reacondicionado" in product_caption:
            condition = "https://schema.org/RefurbishedCondition"
        elif "open" in product_caption:
            condition = "https://schema.org/OpenBoxCondition"
        else:
            condition = "https://schema.org/NewCondition"

        if len(variations_tags) <= 3:
            product_data = json.loads(
                soup.findAll("script", {"type": "application/ld+json"})[2].text
            )

            if "open" in product_data["brand"]["name"].lower():
                condition = "https://schema.org/OpenBoxCondition"

            name = product_data["name"]
            sku = product_data["sku"]
            picture_urls = product_data["image"]
            offer = product_data["offers"][0]
            key = str(re.search(r"variant=(\d+)", offer["url"]).groups()[0])
            stock = -1 if (offer["availability"] == "http://schema.org/InStock") else 0
            price = Decimal(offer["price"]).quantize(0)

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
                condition=condition,
            )
            products.append(p)
        else:
            variations = json.loads(variations_tags[-1].text)
            for variation in variations:
                name = variation["name"]

                if "grado" in name.lower():
                    condition = "https://schema.org/RefurbishedCondition"

                key = str(variation["id"])
                stock = -1 if variation["available"] else 0
                price = Decimal(variation["price"] / 100).quantize(0)
                sku = variation["sku"]

                if not sku:
                    continue

                if variation["featured_image"]:
                    picture_urls = ["https:" + variation["featured_image"]["src"]]
                else:
                    picture_urls = None

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
                    condition=condition,
                )
                products.append(p)

        return products

    @classmethod
    def preflight(cls, extra_args=None):
        session = session_with_proxy(extra_args)

        response = session.get("https://backonline.cl/collections")
        soup = BeautifulSoup(response.text, "lxml")

        collection_cells = soup.findAll("li", "collection-list__item")
        collection_urls = []

        for collection_cell in collection_cells:
            collection_link = collection_cell.find("a")

            if "href" not in collection_link.attrs:
                continue

            cell_label = collection_cell.find("h3").text.upper()
            collection_url = "https://backonline.cl" + collection_link["href"]
            collection_urls.append((cell_label, collection_url))

        return {"collection_urls": collection_urls}
