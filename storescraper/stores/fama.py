import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Fama(Store):
    @classmethod
    def categories(cls):
        return [WASHING_MACHINE]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [["40", WASHING_MACHINE]]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 0
            while True:
                if page > 10:
                    raise Exception("page overflow")
                url_webpage = (
                    "https://www.fama.com.uy/productos/productos"
                    ".php?id_marca={}&pagina={}".format(url_extension, page)
                )
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "lxml")
                product_containers = soup.findAll("article", "prod_item")

                if not product_containers:
                    if page == 1:
                        logging.warning("Empty category")
                    break
                for container in product_containers:
                    product_url = container.find("a")["href"]
                    product_urls.append("https://www.fama.com.uy" + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", {"itemprop": "name"}).text
        key_tag = soup.find("input", {"name": "ids[]"})

        if not key_tag:
            return []

        key = key_tag["value"]
        sku = soup.find("div", {"itemprop": "sku"}).text.strip()
        stock = -1
        price = Decimal(soup.find("span", {"itemprop": "price"}).text.strip())
        picture_urls = [
            tag["src"] for tag in soup.find("div", "galeria").findAll("img")
        ]
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
        )
        return [p]
