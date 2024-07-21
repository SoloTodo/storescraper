import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import (
    html_to_markdown,
    session_with_proxy,
    magento_picture_urls,
)


class Artefacta(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)

        if category != TELEVISION:
            return []

        page = 1
        product_urls = []
        done = False

        while not done:
            if page > 10:
                raise Exception("Page overflow")

            url = (
                "https://www.artefacta.com/c?marca=42974&p={}&" "product_list_limit=36"
            ).format(page)
            print(url)
            soup = BeautifulSoup(session.get(url).text, "lxml")
            products = soup.findAll("li", "item product product-item")

            if not products:
                if page == 1:
                    raise Exception("Empty path: " + url)
                break

            for product in products:
                try:
                    product_url = product.find("a")["href"]
                except KeyError:
                    # Skip the template tag
                    continue

                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, "lxml")

        name = soup.find("span", {"itemprop": "name"}).text.strip()
        sku = soup.find("div", {"itemprop": "sku"}).text.strip()
        stock = -1

        price = Decimal(
            soup.find("span", {"data-price-type": "finalPrice"})
            .find("span", "price")
            .text.replace("$", "")
            .replace(",", "")
        )
        picture_urls = magento_picture_urls(soup)

        description = html_to_markdown(str(soup.find("div", "description")))

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
            "USD",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
