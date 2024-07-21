import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class GamersColombia(Store):
    @classmethod
    def categories(cls):
        return [MONITOR]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != MONITOR:
            return []
        session = session_with_proxy(extra_args)

        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow")
            url = "https://www.gamerscolombia.com/tienda?brands%5B%5D=9&page={}".format(
                page
            )
            print(url)
            res = session.get(url)
            soup = BeautifulSoup(res.text, "lxml")
            product_containers = soup.findAll("div", "product-card")
            if not product_containers:
                break

            for product in product_containers:
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        key_match = re.search(r"addCart\((\d+)", response.text)

        if not key_match:
            return []

        key = key_match.groups()[0]
        soup = BeautifulSoup(response.text, "lxml")
        price_tag = soup.find("div", "cardPriceProduct")
        price = Decimal(price_tag.find("h3").text.replace("$", "").replace(",", ""))
        stock = -1
        name = soup.find("h2").text.strip()
        picture_urls = [x["href"] for x in soup.find("div", "fotorama").findAll("a")]

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
            picture_urls=picture_urls,
        )
        return [p]
