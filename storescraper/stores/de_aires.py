import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import AIR_CONDITIONER


class DeAires(StoreWithUrlExtensions):
    # ONLY CONSIDERS LG PRODUCTS

    url_extensions = [
        ["categoria-producto/lg", AIR_CONDITIONER],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        del session.headers["Accept-Encoding"]
        page = 1

        while True:
            if page > 10:
                raise Exception("Page overflow")

            url = "https://deaires.cl/{}/page/{}/".format(url_extension, page)
            print(url)
            response = session.get(url)

            soup = BeautifulSoup(response.text, "html.parser")
            products = soup.findAll("li", "product")

            if not products:
                break

            for product in products:
                product_url = product.find("a", "woocommerce-LoopProduct-link")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        del session.headers["Accept-Encoding"]
        res = session.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[-1]
        product_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )
        name = product_data["name"]
        if product_data["offers"][0]["availability"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        price = Decimal(product_data["offers"][0]["priceSpecification"]["price"])

        picture_urls = [
            x.find("img")["src"] for x in soup.findAll("picture", "wp-post-image")
        ]

        description = html_to_markdown(product_data["description"])

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
            "CLP",
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
