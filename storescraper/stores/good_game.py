import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    COMPUTER_CASE,
    POWER_SUPPLY,
    CPU_COOLER,
    VIDEO_CARD,
    MOUSE,
    HEADPHONES,
    GAMING_CHAIR,
    STORAGE_DRIVE,
    NOTEBOOK,
    GAMING_DESK,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class GoodGame(StoreWithUrlExtensions):
    url_extensions = [
        ["588-gabinetes", COMPUTER_CASE],
        ["594-kit-gabinetes", COMPUTER_CASE],
        ["584-fuentes-de-poder", POWER_SUPPLY],
        ["587-sistemas-de-enfriamiento", CPU_COOLER],
        ["590-tarjetas-de-video", VIDEO_CARD],
        ["586-teclados-mouse", MOUSE],
        ["585-audio-video", HEADPHONES],
        ["589-sillas-gamer", GAMING_CHAIR],
        ["595-almacenamiento", STORAGE_DRIVE],
        ["601-notebook", NOTEBOOK],
        ["592-escritorios-gamer", GAMING_DESK],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        done = False
        while not done:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://good-game.cl/{}?page={}".format(url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-container")

            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break

            for container in product_containers:
                product_url = container.find("a")["href"]

                if product_url in product_urls:
                    done = True
                    break

                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        if response.status_code == 500:
            return []
        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", {"itemprop": "name"}).text
        sku = soup.find("input", {"name": "id_product"})["value"]

        availability_text = soup.find("span", {"id": "availability_value"}).text.upper()

        for unavailable_kw in ["PRODUCTO SIN STOCK", "PREVENTA"]:
            if unavailable_kw in availability_text:
                stock = 0
                break
        else:
            stock = -1

        normal_price = Decimal(
            remove_words(soup.find("span", {"id": "our_price_display"}).text)
        )
        offer_price = Decimal(
            remove_words(soup.find("ul", "multipleprices").find("span").text)
        )

        if offer_price > normal_price:
            return []

        picture_urls = [
            tag["src"] for tag in soup.find("div", {"id": "views_block"}).findAll("img")
        ]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            "CLP",
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
