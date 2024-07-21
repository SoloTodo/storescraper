import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Divino(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # ONLY CONSIDERS LG SKUs

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        discovered_urls = []
        page = 1

        while True:
            if page >= 50:
                raise Exception("Page overflow")

            endpoint = (
                "https://www.divino.com.uy/catalogo?skumarca=lg&js=1" "&pag={}"
            ).format(page)
            res = session.get(endpoint)

            if res.url != endpoint:
                break

            soup = BeautifulSoup(res.text, "lxml")

            for product_entry in soup.findAll("div", "it"):
                product_url = product_entry.find("a")["href"]
                discovered_urls.append(product_url)

            page += 1

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        soup = BeautifulSoup(res.text, "lxml")
        json_tag = soup.find("div", {"id": "_jsonDataFicha_"})
        product_json = json.loads(json_tag.text)
        name = product_json["nombreCompleto"]
        key = product_json["sku"]["fen"]
        sku = product_json["sku"]["com"]
        stock = -1 if product_json["variante"]["tieneStock"] else 0
        price = Decimal(product_json["precioMonto"]).quantize(Decimal("0.01"))
        picture_urls = ["https:" + product_json["variante"]["img"]["u"]]

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
        )

        return [p]
