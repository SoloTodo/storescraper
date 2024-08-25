from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import (
    session_with_proxy,
    html_to_markdown,
    magento_picture_urls,
)


class GolloTienda(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # KEEPS ONLY LG PRODUCTS
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            if page > 10:
                raise Exception("Page overflow")

            url = f"https://www.gollo.com/c/LG?p={page}"
            print(url)

            response = session.get(url)
            soup = BeautifulSoup(response.text, "lxml")
            container = soup.find("div", "products")

            if not container:
                if page == 1:
                    raise Exception("Empty store")
                break

            for item in container.findAll("li", "item"):
                product_url = item.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        data = response.text
        soup = BeautifulSoup(data, "lxml")

        name = soup.find("span", {"data-ui-id": "page-title-wrapper"}).text.strip()
        sku = (
            soup.find("div", "product attribute sku").find("div", "value").text.strip()
        )

        if soup.find("div", "stock available").find("span").text == "Disponible":
            stock = -1
        else:
            stock = 0

        price = Decimal(
            soup.find("span", {"data-price-type": "finalPrice"})["data-price-amount"]
        )

        description = html_to_markdown(
            str(soup.find("div", "additional-attributes-wrapper"))
        )

        description += "\n\n{}".format(
            html_to_markdown(str(soup.find("div", "product attribute description")))
        )

        description += "\n\n{}".format(
            html_to_markdown(str(soup.find("div", "dimensions-wrapper")))
        )

        picture_urls = magento_picture_urls(soup)

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
            "CRC",
            sku=sku,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
