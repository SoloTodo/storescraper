import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class AlbionHaus(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [TELEVISION]
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception("page overflow")
                url_webpage = "https://albionhaus.com/tienda/page/{}/?s=LG&post_type=product&filter_marca=lg".format(
                    page
                )
                print(url_webpage)

                data = session.get(url_webpage)
                soup = BeautifulSoup(data.text, "lxml")
                product_containers = soup.findAll("div", "wd-product")
                if not product_containers:
                    if page == 1:
                        logging.warning("Empty category")
                    break
                for container in product_containers:
                    product_url = container.find("a")["href"]
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )["@graph"][-1]

        name = json_data["name"]
        description = json_data["description"]
        key = str(json_data["sku"])
        stock = (
            -1
            if json_data["offers"][0]["availability"] == "http://schema.org/InStock"
            else 0
        )
        price = Decimal(json_data["offers"][0]["price"])
        picture_urls = [json_data["image"]]

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
            sku=key,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
