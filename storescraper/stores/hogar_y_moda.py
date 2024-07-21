import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class HogarYModa(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            if page >= 15:
                raise Exception("Page overflow")

            url = "https://hogarymoda.com.co/shop/page/{}/?s=LG".format(page)

            soup = BeautifulSoup(session.get(url).text, "lxml")
            products_container = soup.findAll("li", "product")

            if not products_container:
                if page == 1:
                    raise Exception("Empty site: {}".format(url))
                break

            for product in products_container:
                product_name = product.find("h2").text.upper()
                if "LG" not in product_name:
                    continue
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, "lxml")
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]

        product_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )
        product_data = product_data["@graph"][1]
        name = product_data["name"]
        sku = product_data["sku"]

        offer = product_data["offers"][0]
        if offer["availability"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        price = Decimal(product_data["offers"][0]["price"])
        description = product_data["description"]
        picture_urls = [x["data-src"] for x in soup.findAll("img", "owl-lazy")]

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
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
