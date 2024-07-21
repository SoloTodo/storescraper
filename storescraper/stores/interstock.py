import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    RAM,
    UPS,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class Interstock(StoreWithUrlExtensions):
    url_extensions = [
        ["computacion-y-ti", RAM],
        ["respaldo-de-energia", UPS],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        page = 1

        while True:
            if page >= 10:
                raise Exception("Page overflow: " + url_extension)

            url_webpage = (
                "https://interstock.cl/categoria-producto/{}/" "page/{}"
            ).format(url_extension, page)

            print(url_webpage)
            response = session.get(url_webpage)

            if response.status_code == 404:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break

            soup = BeautifulSoup(response.text, "lxml")
            products_tags = soup.findAll("ul", "products")

            if not products_tags:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break

            # if len(products_tags) < 2:
            # There are two product sections ina normal page, the
            # second one is just random offers
            # break

            link_containers = products_tags[0].findAll("li", "product")

            for link_container in link_containers:
                product_url = link_container.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, "lxml")

        name = soup.find("h1", "product_title").text.strip()
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
        sku_tag = soup.find("span", "sku")
        if sku_tag:
            sku = soup.find("span", "sku").text.strip()
        else:
            sku = None
        qty_input = soup.find("input", "input-text qty text")
        if qty_input:
            if qty_input["max"]:
                stock = int(qty_input["max"])
            else:
                stock = -1
        else:
            if soup.find("button", "single_add_to_cart_button"):
                stock = 1
            else:
                stock = 0

        product_container = soup.find("p", "price")
        price = Decimal(
            remove_words(
                product_container.find("span", "woocommerce-Price-amount").text
            )
        )
        description = html_to_markdown(
            str(soup.find("div", "elementor-widget-woocommerce-product-data-tabs"))
        )
        picture_urls = [
            tag.find("a")["href"]
            for tag in soup.findAll("div", "woocommerce-product-gallery__image")
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
            part_number=sku,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
