from decimal import Decimal
import json
import logging
import re

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Novey(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only interested in LG products

        session = session_with_proxy(extra_args)
        product_urls = []
        if TELEVISION != category:
            return []

        url = "https://lusearchapi-na.hawksearch.com/sites/novey/?searchText=LG&mpp=300"
        print(url)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        product_containers = soup.findAll("div", "hawk-item-list__item")

        if not product_containers:
            logging.warning("Empty category:" + url)

        for container in product_containers:
            product_url = container.find("a")["href"]
            product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        product_data = re.search(
            r"CCRZ.detailData.jsonProductData = {([\S\s]+?)};", response.text
        )

        if not product_data:
            return []

        product_json = json.loads("{" + product_data.groups()[0] + "}")["product"]

        if product_json["canAddtoCart"]:
            stock = -1
        else:
            stock = 0

        prodBean = product_json["prodBean"]

        name = prodBean["name"]
        sku = prodBean["sku"]
        key = prodBean["id"]
        price = Decimal(str(prodBean["price"]))
        description = prodBean.get("filterData", None)

        picture_urls = [i["uri"] for i in prodBean.get("EProductMediasS", [])]

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
            "USD",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
