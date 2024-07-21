import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Electroban(Store):
    @classmethod
    def categories(cls):
        return [
            "Television",
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != "Television":
            return []

        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/80.0.3987.149 "
            "Safari/537.36"
        )

        product_urls = []
        page = 1

        while True:
            if page >= 15:
                raise Exception("Page overflow")
            # Only get LG products
            url_webpage = (
                "https://www.electroban.com.py/get-productos?"
                "page={}&marcas=30".format(page)
            )

            print(url_webpage)
            data = session.get(url_webpage).text
            product_containers = json.loads(data)["paginacion"]["data"]

            if not product_containers:
                break

            for product in product_containers:
                product_url = product["url_ver"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/80.0.3987.149 "
            "Safari/537.36"
        )
        soup = BeautifulSoup(session.get(url).text, "lxml")
        name = soup.find("div", "product-details").find("h1", "product-title").text
        sku = soup.find("span", "product-cod").text.split(":")[1].strip()
        stock = -1
        if soup.find("div", "product-price").find("span", "old-price"):
            price = Decimal(
                soup.find("div", "product-price")
                .text.strip()
                .split(" *")[0]
                .replace("Gs.", "")
                .replace(".", "")
                .replace("*", "")
                .strip()
            )
        else:
            price = Decimal(
                soup.find("div", "product-price")
                .text.strip()
                .replace("Gs.", "")
                .replace(".", "")
                .replace("*", "")
                .strip()
            )

        picture_urls = [
            tag["src"] for tag in soup.find("div", "slider-single").findAll("img")
        ]

        return [
            Product(
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
        ]
