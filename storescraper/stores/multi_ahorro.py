import json
import logging
import math
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MultiAhorro(Store):
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
            url_webpage = (
                "https://www.multiahorro.com.uy/catalogo?q=lg&"
                "marca=lg&js=1&pag={}".format(page)
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            page_numbers = math.ceil(int(soup.find("div", "tot").text.split()[0]) / 12)
            for i in range(page_numbers):
                if i > 0:
                    url_webpage = (
                        "https://www.multiahorro.com.uy/catalogo?"
                        "q=lg&marca=lg&js=1&pag={}".format(i + 1)
                    )
                    data = session.get(url_webpage).text
                    soup = BeautifulSoup(data, "lxml")
                product_containers = soup.find("div", {"id": "catalogoProductos"})
                if not product_containers:
                    if page == 1:
                        logging.warning("Empty category: " + local_category)
                    break
                for container in product_containers.findAll("div", "it"):
                    product_url = container.find("a")["href"]
                    product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        json_data = json.loads(soup.find("div", {"id": "_jsonDataFicha_"}).text)
        name = json_data["producto"]["nombre"]
        sku = json_data["producto"]["codigo"]
        stock = -1 if json_data["variante"]["tieneStock"] else 0
        price = Decimal(json_data["precioMonto"])
        picture_urls = [
            "http:" + tag["src"]
            for tag in soup.find("ul", "lst lstThumbs").findAll("img")
        ]
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
            "USD",
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
