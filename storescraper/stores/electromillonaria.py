import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, session_with_proxy


class Electromillonaria(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow")
            url = "https://electromillonaria.co/product-brand/lg/page/{}/".format(page)
            print(url)
            res = session.get(url)
            if res.status_code == 404:
                break
            soup = BeautifulSoup(res.text, "lxml")

            for product in soup.find("div", "main-products").findAll(
                "section", "product"
            ):
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
        qty_input = soup.find("input", "input-text qty text")

        if not qty_input:
            stock = 0
        else:
            max_qty = qty_input["max"]
            stock = int(max_qty) if max_qty else -1

        name = soup.find("h1", "product_title").text
        sku = str(soup.find("span", "sku").text.strip())
        price = Decimal(remove_words(soup.find("p", "price").findAll("bdi")[-1].text))
        description = html_to_markdown(
            soup.find(
                "div", {"data-widget_type": "woocommerce-product-content.default"}
            ).text
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
            "COP",
            sku=sku,
            description=description,
        )
        return [p]
