from bs4 import BeautifulSoup
from decimal import Decimal
import json
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import VIDEO_CARD


class XtremeComponents(StoreWithUrlExtensions):
    url_extensions = [
        ["compra-inmediata", VIDEO_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        page = 1

        while True:
            if page > 10:
                raise Exception("Page overflow")

            url = f"https://xtremecomponents.cl/product-category/{url_extension}/page/{page}"
            print(url)
            response = session.get(url)

            if response.status_code == 404:
                break

            soup = BeautifulSoup(response.text, "lxml")
            products = soup.findAll("li", "product")

            for product in products:
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, "lxml")
        response = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )

        for node in response["@graph"]:
            if node["@type"] == "Product":
                product_data = node
                break
        else:
            raise Exception("No product tag found")

        name = product_data["name"]

        assert len(product_data["offers"]) == 1

        offer = product_data["offers"][0]
        stock = -1 if offer["availability"] == "http://schema.org/InStock" else 0
        price = Decimal(offer["price"])
        sku = str(product_data["sku"])
        description = html_to_markdown(product_data["description"])
        picture_urls = [
            soup.find("div", "woocommerce-product-gallery__image").find("a")["href"]
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
            "CLP",
            sku=sku,
            description=description,
            picture_urls=picture_urls,
            condition="https://schema.org/RefurbishedCondition",
        )

        return [p]
