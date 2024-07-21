from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class TiendaAmiga(Store):
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
        while True:
            if page > 20:
                raise Exception("Page overflow")

            url_webpage = (
                "https://www.tiendaamiga.com.bo/catalogsearch/resu"
                "lt/index/?manufacturer=6509&p={}&q=lg+lg".format(page)
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")

            product_containers = soup.findAll("li", "product")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category")
                break
            for container in product_containers:
                product_urls.append(container.find("a")["href"])
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
        price = Decimal(
            soup.find("span", {"id": f"product-price-{key}"})["data-price-amount"]
        )

        if soup.find("div", "stock available") or soup.find("p", "stock available"):
            stock = -1
        else:
            stock = 0

        table = soup.find("div", "table-wrapper")
        description = None
        part_number = None
        if table:
            description = html_to_markdown(table.text)
            if table.find("td", {"data-th": "Modelo"}):
                part_number = table.find("td", {"data-th": "Modelo"}).text

        picture_urls = []
        picture_json = json.loads(
            "{"
            + re.search(
                r"\"mage\/gallery\/gallery\": {([\S\s]+)\"fullscreen", response.text
            ).groups()[0]
            + '"xd": "xd"}'
        )

        for p in picture_json["data"]:
            picture_urls.append(p["img"])

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
            "BOB",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number,
        )
        return [p]
