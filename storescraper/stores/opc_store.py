from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import ALL_IN_ONE, MONITOR, NOTEBOOK, TABLET
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class OpcStore(StoreWithUrlExtensions):
    url_extensions = [
        ["asus", NOTEBOOK],
        ["dell", NOTEBOOK],
        ["hp", NOTEBOOK],
        ["outlet", NOTEBOOK],
        ["notebook", NOTEBOOK],
        ["notebook-portada", NOTEBOOK],
        ["notebook-tradicional", NOTEBOOK],
        ["notebook-lenovo", NOTEBOOK],
        ["ofertas-outlet", NOTEBOOK],
        ["open-box", NOTEBOOK],
        ["open-box-2", NOTEBOOK],
        ["chromebook", NOTEBOOK],
        ["notebook-corporativo", NOTEBOOK],
        ["tablet", TABLET],
        ["open-box-1", TABLET],
        ["all-in-one", ALL_IN_ONE],
        ["dell-aio", ALL_IN_ONE],
        ["hp-aio", ALL_IN_ONE],
        ["lenovo-aio", ALL_IN_ONE],
        ["monitores", MONITOR],
        ["monitores-hp", MONITOR],
        ["monitores-lenovo", MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://www.opcstore.cl/collections/{}?" "page={}".format(
                url_extension, page
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("li", "grid__item")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append("https://www.opcstore.cl" + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("input", {"name": "id"})["value"]

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )

        name = json_data["name"]
        sku = json_data.get("sku", None)
        description = json_data["description"]

        if "caja abierta" in name.lower():
            condition = "https://schema.org/RefurbishedCondition"
        else:
            condition = "https://schema.org/NewCondition"

        offer = json_data["offers"][0]

        price = Decimal(offer["price"])

        if offer["availability"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        if not price and not stock:
            return []

        picture_urls = []
        picture_container = soup.find("div", "product-media-modal__content")
        for i in picture_container.findAll("img"):
            picture_urls.append("https:" + i["src"])

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
            condition=condition,
        )
        return [p]
