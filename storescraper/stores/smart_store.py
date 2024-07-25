import html
import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import (
    HEADPHONES,
    MOUSE,
    SOLID_STATE_DRIVE,
    TABLET,
    USB_FLASH_DRIVE,
    VIDEO_GAME_CONSOLE,
    WEARABLE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy


class SmartStore(StoreWithUrlExtensions):
    url_extensions = [
        ["smart-kids/educacion/accesorios-de-computacion", MOUSE],
        ["smart-kids/educacion/mouse-y-teclados", MOUSE],
        ["smart-kids/educacion/tablets-y-celulares", TABLET],
        ["smart-kids/entretencion/gamers", VIDEO_GAME_CONSOLE],
        ["smart-kids/entretencion/smartwatches", WEARABLE],
        ["smart-life/accesorios-tecnologia/discos-duros", SOLID_STATE_DRIVE],
        ["smart-life/accesorios-tecnologia/memorias-y-pendrives", USB_FLASH_DRIVE],
        ["smart-life/accesorios-tecnologia/perifericos-computacion", MOUSE],
        ["smart-life/aire-libre/audifonos", HEADPHONES],
        ["smart-life/wearables/smartbands", WEARABLE],
        ["smart-life/wearables/smartphones-y-tablets", TABLET],
        ["smart-life/wearables/smartwatches", WEARABLE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            url_webpage = f"https://www.smartstore.cl/{url_extension}?page={page}"
            print(url_webpage)

            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            data = soup.findAll("script")[8].text
            links = re.findall(r'"link":"(\\u002F[^"]+)"', data)

            if not links:
                if page == 1:
                    logging.warning("empty category: " + url_extension)
                break

            links = [link.encode("utf-8").decode("unicode_escape") for link in links]

            for link in links:
                product_url = f"https://www.smartstore.cl{link}"
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        json_data = soup.find("script", {"type": "application/ld+json"})

        if json_data is None:
            return []

        json_data = json.loads(json_data.text)
        products = []

        for offer in json_data["offers"]["offers"]:
            name = json_data["name"]
            sku = offer["sku"]
            stock = -1 if offer["availability"] == "http://schema.org/InStock" else 0
            price = Decimal(offer["price"])
            picture_urls = [
                img["src"]
                for img in soup.find("div", {"swiper-wrapper"}).findAll("img")
            ]
            description = html_to_markdown(html.unescape(json_data["description"]))

            product = Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                price,
                price,
                "CLP",
                sku=sku,
                picture_urls=picture_urls,
                description=description,
            )

            products.append(product)

        return products
