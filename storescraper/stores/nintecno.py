import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    MONITOR,
    HEADPHONES,
    STEREO_SYSTEM,
    VIDEO_GAME_CONSOLE,
    NOTEBOOK,
    CELL,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Nintecno(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos", HEADPHONES],
        ["parlantes-inalambricos", STEREO_SYSTEM],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["notebooks", NOTEBOOK],
        ["monitores", MONITOR],
        ["parlantes-inteligentes", STEREO_SYSTEM],
        ["celulares", CELL],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        page = 1

        while True:
            if page >= 50:
                raise Exception("Page overflow: " + url_extension)

            url_webpage = (
                "https://nintecno.cl/index.php/"
                "product-category/{}/?page={}".format(url_extension, page)
            )

            print(url_webpage)
            response = session.get(url_webpage)

            soup = BeautifulSoup(response.text, "lxml")
            link_containers = soup.findAll("div", "product")

            if not link_containers:
                logging.warning("Empty category: " + url_webpage)
                break

            for link_container in link_containers:
                product_url = link_container.find("a")["href"]
                if product_url in product_urls:
                    return product_urls
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, "lxml")

        json_tag = soup.find("script", {"type": "application/ld+json"})
        json_data = json.loads(json_tag.text)["@graph"][1]
        name = json_data["name"].strip()
        key = str(json_data["sku"])
        description = json_data["description"]

        if json_data["offers"][0]["availability"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        prices_table_tag_cells = soup.find("table", "precios-adicionales").findAll("td")
        assert len(prices_table_tag_cells) == 4

        normal_price = Decimal(remove_words(prices_table_tag_cells[3].text))
        offer_price = Decimal(remove_words(prices_table_tag_cells[1].text))

        picture_urls = [
            x.find("a")["href"]
            for x in soup.findAll("div", "woocommerce-product-gallery__image")
        ]

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
            sku=key,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
