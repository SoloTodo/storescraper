import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from curl_cffi import requests


class Mercacentro(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []
        session = requests.Session(impersonate="chrome120")
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        product_urls = []
        res = session.get("https://www.mercacentro.com/search/?k=LG&p=1&c=0&sp=12")
        soup = BeautifulSoup(res.text, "lxml")
        product_containers = soup.findAll("div", "dpr_container")

        for product in product_containers:
            product_url = "https://www.mercacentro.com" + product.find("a")["href"]
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = requests.Session(impersonate="chrome120")
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        product_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )

        name = product_data["name"]
        key = product_data["sku"]
        description = product_data["description"]
        ean = product_data["gtin13"]
        price = Decimal(product_data["offers"]["lowPrice"])

        if product_data["offers"]["availability"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0

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
            "COP",
            sku=key,
            description=description,
            ean=ean,
        )
        return [p]
