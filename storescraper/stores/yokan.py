import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD, MOUSE, VIDEO_GAME_CONSOLE, CELL
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Yokan(StoreWithUrlExtensions):
    url_extensions = [
        ["apple", CELL],
        ["tecno/consolas", VIDEO_GAME_CONSOLE],
        ["tecno/tvid", VIDEO_CARD],
        ["tecno/mouse", MOUSE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow")
            url_webpage = "https://yokan.cl/product-category/{}/page/{}".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-small")

            if not product_containers:
                if page == 1:
                    logging.warning("empty category: " + url_extension)
                break

            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", "product-title").text.strip()
        picture_urls = [
            tag["src"] for tag in soup.find("div", "product-gallery").findAll("img")
        ]

        variants_tag = soup.find("form", "variations_form")
        products = []
        if variants_tag:
            variations_data = json.loads(variants_tag["data-product_variations"])

            for variant in variations_data:
                if variant["attributes"]:
                    variant_name = "{} ({})".format(
                        name, variant["attributes"]["attribute_style"]
                    )
                else:
                    variant_name = name

                key = str(variant["variation_id"])
                sku = variant["sku"]

                # Yokan website has a bug where a variant with no name cannot
                # be purchased
                if not variant["attributes"]:
                    stock = 0
                else:
                    stock = variant["max_qty"] or 0
                offer_price = Decimal(variant["display_price"])
                normal_price = (offer_price * Decimal("1.05")).quantize(0)
                p = Product(
                    variant_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    key,
                    stock,
                    normal_price,
                    offer_price,
                    "CLP",
                    sku=sku,
                    picture_urls=picture_urls,
                )
                products.append(p)
        else:
            key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[-1]
            sku_tag = soup.find("span", "sku")

            if sku_tag:
                sku = soup.find("span", "sku").text.strip()
            else:
                sku = None

            stock = 0
            stock_selector = soup.find("select", "slw_item_stock_location")
            if stock_selector:
                for option in stock_selector.findAll("option"):
                    if "Chile" not in option.text:
                        continue
                    stock = int(option["data-quantity"])
                    break

            price_container = soup.find("p", "price")
            if price_container.find("ins"):
                offer_price = Decimal(
                    remove_words(price_container.find("ins").text.strip())
                )
            else:
                offer_price = Decimal(remove_words(price_container.text.strip()))

            normal_price = (offer_price * Decimal("1.05")).quantize(0)

            p = Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                normal_price,
                offer_price,
                "CLP",
                sku=sku,
                picture_urls=picture_urls,
            )
            products.append(p)
        return products
