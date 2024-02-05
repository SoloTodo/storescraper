import re
from decimal import Decimal
import logging

from bs4 import BeautifulSoup

from storescraper.categories import MONITOR
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class PlayPower(StoreWithUrlExtensions):
    url_extensions = [
        ["all", MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://playpower.cl/collections/{}?page={}".format(
                url_extension, page
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html.parser")
            product_containers = soup.findAll("li", "grid__item")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_path = container.find("a")["href"]
                product_urls.append("https://playpower.cl" + product_path)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        name_tag = soup.find("h3", {"data-product-type": "title"})

        if not name_tag:
            return []

        name = name_tag.text.strip()
        key, stock_text = re.search(
            r'quantity: \["(\d+):(\d)"]', response.text
        ).groups()
        stock = int(stock_text)
        price = Decimal(
            remove_words(soup.find("div", {"data-product-type": "price"}).text.strip())
        )
        picture_urls = [
            "https:" + x.find("img")["src"]
            for x in soup.find("div", "pf-media-slider").findAll(
                "div", "pf-slide-main-media"
            )
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
            picture_urls=picture_urls,
        )
        return [p]
