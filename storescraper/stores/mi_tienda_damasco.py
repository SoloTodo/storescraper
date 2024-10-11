import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class MiTiendaDamasco(StoreWithUrlExtensions):
    url_extensions = [
        ["lg", TELEVISION],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            if page > 20:
                raise Exception("page overflow")

            url_webpage = f"https://www.damascovzla.com/{url_extension}?page={page}"
            print(url_webpage)

            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")

            product_containers = soup.findAll(
                "section", "vtex-product-summary-2-x-container"
            )

            if not product_containers:
                if page == 1:
                    logging.warning("empty category")
                break

            for container in product_containers:
                product_urls.append(
                    f"https://www.damascovzla.com{container.find('a')['href']}"
                )

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        reference_name = re.search(r"/([^/]+)/p", url).group(1)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        state_match = re.search("__STATE__ = (.+)", response.text)
        json_data = json.loads(state_match.groups()[0])
        product_data = json_data[f"Product:{reference_name}.items.0"]

        name = product_data["name"]
        key = product_data["itemId"]
        sku = product_data["ean"]
        stock = -1 if soup.find("span", "vtex-add-to-cart-button-0-x-buttonText") else 0
        price_data = json_data[f"$Product:{reference_name}.priceRange.sellingPrice"]
        low_price = price_data["lowPrice"]

        if not low_price:
            return []

        price = Decimal(price_data["lowPrice"])
        description = html_to_markdown(
            json_data[f"Product:{reference_name}"]["description"]
        )
        picture_ids = [x["id"].split("Image:")[1] for x in product_data["images"]]
        picture_urls = [
            f"https://damasco.vtexassets.com/arquivos/ids/{picture}-1600-1600"
            for picture in picture_ids
        ]

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
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
