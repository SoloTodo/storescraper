from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import CELL, NOTEBOOK, VIDEO_CARD
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import remove_words, session_with_proxy, html_to_markdown


class SercoImport(StoreWithUrlExtensions):
    preferred_discover_urls_concurrency = 2
    preferred_products_for_url_concurrency = 2

    url_extensions = [
        ["gamer", NOTEBOOK],
        ["computacion", NOTEBOOK],
        ["celular-y-accesorios", CELL],
        ["componentes", VIDEO_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://sercoimport.cl/product-category/{}/page/{}/".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-type-simple")

            if not product_containers:
                if page == 1:
                    logging.warning("empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a", "db")["href"]
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
        name = soup.find("h1", "product_title").text.strip()
        if soup.find("button", {"name": "add-to-cart"}):
            stock = -1
        else:
            stock = 0
        price_tag = soup.find("span", "woocommerce-Price-amount")
        price = Decimal(remove_words(price_tag.text))
        sku_tag = soup.find("span", "sku")
        if sku_tag:
            sku = sku_tag.text.strip()
        else:
            sku = None
        picture_urls = [
            x["src"]
            for x in soup.findAll("img", "attachment-shop_single size-shop_single")
        ]
        description = html_to_markdown(
            str(soup.find("div", "woocommerce-Tabs-panel--additional_information"))
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
            "CLP",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
