import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    AIR_CONDITIONER,
    OVEN,
    REFRIGERATOR,
    STEREO_SYSTEM,
    TELEVISION,
    WASHING_MACHINE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class AlcaColombia(StoreWithUrlExtensions):
    url_extensions = [
        ["smart_tv", TELEVISION],
        ["aires", AIR_CONDITIONER],
        ["cocina", OVEN],
        ["lavadoras-y-secadoras", WASHING_MACHINE],
        ["refrigeracion", REFRIGERATOR],
        ["audio", STEREO_SYSTEM],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        product_urls = []
        page = 1

        while True:
            if page > 10:
                raise Exception("Page overflow")

            url = f"https://alcaltda.com/page/{page}/?s=LG&post_type=product&product_cat={url_extension}"
            print(url)

            res = session.get(url)
            soup = BeautifulSoup(res.text, "lxml")
            product_containers = soup.findAll("div", "wd-product")

            if not product_containers:
                break

            for product in product_containers:
                product_name = product.find("h3").text.strip().upper()
                categories = product.find("div", "wd-product-cats").text.strip().upper()

                if "LG" not in product_name and "LG" not in categories:
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
        soup = BeautifulSoup(response.text, "lxml")

        product_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )["@graph"][1]

        name = product_data["name"]
        sku = product_data["sku"]
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]

        assert len(product_data["offers"]) == 1

        offer = product_data["offers"][0]
        price = Decimal(offer["price"])
        description = html_to_markdown(product_data["description"])
        stock_quantity = re.findall(r"\d+", soup.find("p", "stock").text)
        stock = int(stock_quantity[0])
        picture_urls = []
        pictures_container = soup.find("div", "wd-gallery-images")

        for img in pictures_container.findAll("img"):
            if "data-large_image" in img.attrs:
                picture_urls.append(img["data-large_image"])

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
