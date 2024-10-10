from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import (
    session_with_proxy,
    html_to_markdown,
    magento_picture_urls,
    remove_words,
)


class Tecnofacil(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [TELEVISION]

        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = "curl/7.68.0"
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page >= 25:
                    raise Exception("Page overflow")

                url = "https://www.tecnofacil.com.gt/marcas/productos-lg"

                if page > 1:
                    url += "?p={}".format(page)

                print(url)
                response = session.get(url)
                soup = BeautifulSoup(response.text, "lxml")
                product_containers = soup.find("div", "products-grid")

                if not product_containers:
                    break

                for container in product_containers.findAll("li", "product-item"):
                    product_url = container.find("a")["href"]
                    print(product_url)
                    if product_url in product_urls:
                        return product_urls
                    product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = "curl/7.68.0"
        data = session.get(url).text
        soup = BeautifulSoup(data, "lxml")
        sku_container = soup.find("div", {"itemprop": "sku"})

        if not sku_container:
            return []

        sku = sku_container.text.strip()
        key = soup.find("input", {"name": "product"})["value"]
        name = "{} ({})".format(
            soup.find("span", {"itemprop": "name"}).text.strip(), sku
        )

        if not soup.find(
            "img", {"src": "https://www.tecnofacil.com.gt/" "media/marcas/LG.jpg"}
        ):
            stock = 0
        elif soup.find("button", "add-cart"):
            stock = -1
        else:
            stock = 0
        price_container = soup.find("span", "price-wrapper")
        price_integer = int(
            remove_words(
                price_container.find("span", "price-integer").text, blacklist=["Q", ","]
            )
        )
        price_decimal = float(price_container.find("span", "price-decimal").text)
        price = Decimal(price_integer + price_decimal)

        picture_urls = magento_picture_urls(soup)
        description = html_to_markdown(
            str(soup.find("div", "additional-attributes-wrapper"))
        )

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
            "GTQ",
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
