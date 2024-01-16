import json
import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import (
    CELL,
    TABLET,
    HEADPHONES,
    TELEVISION,
    MONITOR,
    WEARABLE,
    VACUUM_CLEANER,
    STEREO_SYSTEM,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class XiaomiOnline(StoreWithUrlExtensions):
    url_extensions = [
        ["smartphones", CELL],
        ["smart-home/tv-monitores-media/televisores", TELEVISION],
        ["smart-home/tv-monitores-media/monitores", MONITOR],
        ["smart-home/mi-pad", TABLET],
        ["smart-home/electrodomesticos/limpieza", VACUUM_CLEANER],
        ["smart-home/televisores", TELEVISION],
        ["estilo-vida/smartwatch-smartband", WEARABLE],
        ["estilo-vida/audio/audifonos", HEADPHONES],
        ["estilo-vida/audio/parlantes", STEREO_SYSTEM],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://xiaomionline.cl/{}?p={}".format(url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "html.parser")
            product_containers = soup.findAll("li", "product-item")

            if not product_containers:
                if page == 1:
                    logging.warning("Emtpy category: " + url_extension)
                break

            for container in product_containers:
                product_url = container.find("a")["href"]
                # The site returns the products of the first page when overflowing
                if product_url in product_urls:
                    return product_urls
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        name = soup.find("h1", "product-name").text.strip()
        key = soup.find("input", {"name": "product"})["value"]
        sku = soup.find("div", "sku").find("span", "value").text.strip()
        stock = -1
        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"]
        )
        part_number = soup.find("td", {"data-th": "MPN"}).text.strip()
        picture_urls = [x["href"] for x in soup.findAll("a", "mt-thumb-switcher")]

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
            "CLP",
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls,
        )
        return [p]
