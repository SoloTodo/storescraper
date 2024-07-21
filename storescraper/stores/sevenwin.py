import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    GAMING_CHAIR,
    HEADPHONES,
    MOUSE,
    MONITOR,
    GAMING_DESK,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Sevenwin(Store):
    @classmethod
    def categories(cls):
        return [GAMING_CHAIR, HEADPHONES, MOUSE, MONITOR, GAMING_DESK]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["seven-win-sillas-gamers", GAMING_CHAIR],
            ["seven-win-audifonos-gamer", HEADPHONES],
            ["seven-win-mouse-gamer", MOUSE],
            ["seven-win-monitor-gamer", MONITOR],
            ["seven-win-escritorios", GAMING_DESK],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception("page overflow: " + url_extension)
                url_webpage = "https://www.sevenwin.cl/{}?page={}".format(
                    url_extension, page
                )
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "lxml")
                product_containers = soup.findAll("div", "product-block")
                if not product_containers:
                    if page == 1:
                        logging.warning("Empty category: " + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find("a")["href"]
                    product_urls.append("https://www.sevenwin.cl" + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", "page-title").text
        key = soup.find("form", {"name": "buy"})["action"].split("/")[-1]
        sku = soup.find("span", "sku_elem").text
        if soup.find("input", "adc") and "preventa" not in name.lower():
            stock = -1
        else:
            stock = 0
        price = Decimal(
            remove_words(soup.find("span", {"id": "product-form-price"}).text)
        )
        picture_urls = [
            tag["src"] for tag in soup.find("div", "product-images").findAll("img")
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
            "CLP",
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
