import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import POWER_SUPPLY, SOLID_STATE_DRIVE, MONITOR


class TechnoKings(StoreWithUrlExtensions):
    url_extensions = [
        ["monitores-gamer", MONITOR],
        ["ssd", SOLID_STATE_DRIVE],
        ["fuente-de-poder", POWER_SUPPLY],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        url = "https://www.technokings.cl/product-categories/{}".format(url_extension)
        print(url)
        response = session.get(url)

        soup = BeautifulSoup(response.text, "lxml")
        products = soup.findAll("li", "product")

        for product in products:
            product_url = product.find("a")["href"]
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, "lxml")
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
        json_container = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )
        json_container = json_container["@graph"][0]
        name = json_container["name"]
        sku = str(json_container["sku"])
        description = html_to_markdown(json_container["description"])
        picture_urls = [json_container["image"]]
        stock_tag = soup.find("p", "stock in-stock")
        if stock_tag:
            stock = int(stock_tag.text.split()[0])
        else:
            stock = 0
        offer_price = Decimal(json_container["offers"][0]["price"])
        normal_price = (offer_price * Decimal("1.03")).quantize(0)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            "CLP",
            sku=sku,
            part_number=sku,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
