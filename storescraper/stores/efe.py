import json
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


class Efe(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1
        done = False

        while not done:
            if page >= 20:
                raise Exception("Page overflow")

            url_webpage = (
                "https://www.efe.com.pe/tecnologia/marcas/" "lg.html?p={}".format(page)
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("li", "product")
            for container in product_containers:
                product_url = container.find("a")["href"]
                if product_url in product_urls:
                    done = True
                    break
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        key = soup.find("input", {"name": "product"})["value"]
        name = soup.find("span", {"itemprop": "name"}).text.strip()
        sku = soup.find("div", {"itemprop": "sku"}).text.strip()
        description = html_to_markdown(str(soup.find("div", "description")))
        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"]
        )

        if soup.find("button", "tocart"):
            stock = -1
        else:
            stock = 0

        picture_urls = magento_picture_urls(soup)

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
            "PEN",
            sku=sku,
            picture_urls=picture_urls,
            part_number=sku,
            description=description,
        )

        return [p]
