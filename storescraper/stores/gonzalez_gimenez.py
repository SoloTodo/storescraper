import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class GonzalezGimenez(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [TELEVISION]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue

        page = 1

        while True:
            if page >= 15:
                raise Exception("Page overflow: ")
            url_webpage = (
                "https://www.gonzalezgimenez.com.py/get-productos?"
                "page={}&marca=8".format(page)
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            product_containers = json.loads(soup.text)

            if not product_containers["paginacion"]["data"]:
                if page == 1:
                    logging.warning("Empty category: " + url_webpage)
                break

            for product in product_containers["paginacion"]["data"]:
                product_url = product["url_ver"]
                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        if "Página Principal" in soup.find("title").text:
            return []

        name = soup.find("meta", {"name": "title"})["content"]
        sku = soup.find("meta", {"property": "product:retailer_item_id"})["content"]
        stock = -1
        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"]
        )
        picture_urls = [tag["href"] for tag in soup.findAll("a", "galeria-modal")]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            "PYG",
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
