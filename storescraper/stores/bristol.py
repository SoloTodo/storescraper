import json

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Bristol(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        if category != TELEVISION:
            return []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow")

            url_webpage = (
                "https://www.bristol.com.py/catalogo?marca=lg" "&js=1&pag={}"
            ).format(page)
            print(url_webpage)
            response = session.get(url_webpage)

            if response.url != url_webpage:
                break

            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "it")
            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        soup = BeautifulSoup(res.text, "lxml")
        product_info = json.loads(soup.find("div", {"id": "_jsonDataFicha_"}).text)

        key = product_info["sku"]["fen"]
        name = product_info["producto"]["nombre"]
        sku = product_info["producto"]["codigo"]
        description = html_to_markdown(str(soup.find("div", "blkDetalle")))
        stock = 0 if soup.find("div", {"id": "plazosProdAgotado"}) else -1
        price = Decimal(product_info["precioMonto"])
        picture_urls = ["https:" + product_info["variante"]["img"]["u"]]

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
            "PYG",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
