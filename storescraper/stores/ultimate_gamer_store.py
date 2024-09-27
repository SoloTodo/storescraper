import logging
import re
import json
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown, remove_words
from storescraper.categories import (
    VIDEO_CARD,
    PROCESSOR,
    MONITOR,
    RAM,
    SOLID_STATE_DRIVE,
    MOTHERBOARD,
    HEADPHONES,
    STORAGE_DRIVE,
    POWER_SUPPLY,
    CPU_COOLER,
    COMPUTER_CASE,
    GAMING_CHAIR,
    NOTEBOOK,
)


class UltimateGamerStore(StoreWithUrlExtensions):
    url_extensions = [
        ["tarjeta-de-video", VIDEO_CARD],
        ["procesadores", PROCESSOR],
        ["placas-madre", MOTHERBOARD],
        ["perifericos", HEADPHONES],
        ["hdd", STORAGE_DRIVE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["monitor", MONITOR],
        ["refrigeracion", CPU_COOLER],
        ["gabinetes", COMPUTER_CASE],
        ["notebook", NOTEBOOK],
        ["memorias", RAM],
        ["almacenamiento/ssd", SOLID_STATE_DRIVE],
        ["productos/sillas", GAMING_CHAIR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            if page >= 10:
                raise Exception("Page overflow")

            url = f"https://www.ugstore.cl/{url_extension}?page={page}"
            print(url)

            response = session.get(url)
            soup = BeautifulSoup(response.text, "lxml")
            items = soup.findAll("div", "product-block")

            if not items:
                if page == 1:
                    logging.warning(f"Emtpy Path: {url}")
                break

            for item in items:
                product_urls.append(f"https://www.ugstore.cl{item.find('a')['href']}")

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        data = soup.find("script", {"type": "application/ld+json"}).text
        clean_data = re.sub(r'"description":\s*"[^"]*",\s*', "", data)
        json_data = json.loads(clean_data)
        product_data = None

        for data in json_data:
            if data["@type"] == "Product":
                product_data = data
                break

        name = product_data["name"]
        normal_price = Decimal(product_data["offers"]["price"])
        offer_price = (normal_price * Decimal("0.96")).quantize(0)
        key = soup.find("meta", {"property": "og:id"})["content"]

        if "PREVENTA" in name.upper() or "PREVENTA" in url.upper():
            stock = 0
        else:
            stock = (
                -1
                if product_data["offers"]["availability"] == "http://schema.org/InStock"
                else 0
            )

        description = html_to_markdown(soup.find("div", "description").text)

        pictures_container = soup.find(
            "swiper-slider", {"product-gallery__slider--main"}
        )

        if not pictures_container:
            picture_urls = [product_data["image"]]
        else:
            picture_urls = [
                img["src"]
                for img in soup.find(
                    "swiper-slider", {"product-gallery__slider--main"}
                ).findAll("img")
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
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
