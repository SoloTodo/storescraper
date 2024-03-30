import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class AlcaColombia(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )

        product_urls = []
        page = 1
        while True:
            if page > 20:
                raise Exception("Page overflow")
            url = "https://alcaltda.com/page/{}/?s=LG&post_type=product".format(page)
            print(url)
            res = session.get(url)
            soup = BeautifulSoup(res.text, "html.parser")
            product_containers = soup.findAll("li", "ast-article-post")
            if not product_containers:
                break

            for product in product_containers:
                product_name = product.find("h2").text.strip().upper()
                if "LG " not in product_name or " LG" not in product_name:
                    continue
                product_url = product.find("a")["href"]
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
        soup = BeautifulSoup(response.text, "html.parser")

        product_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )["@graph"][-1]

        canonical_url_tag = soup.find(
            "link", {"rel": "alternate", "type": "application/json"}
        )
        key = canonical_url_tag["href"].split("/")[-1]
        name = product_data["name"]
        sku = product_data.get("sku", None)
        price = Decimal(product_data["offers"]["price"])
        description = product_data["description"]
        if product_data["offers"]["availability"] == "https://schema.org/InStock":
            stock = -1
        else:
            stock = 0
        picture_urls = [x["url"] for x in product_data["image"]]

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
            part_number=sku,
            description=description,
            picture_urls=picture_urls,
        )
        return [p]
