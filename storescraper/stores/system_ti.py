import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    NOTEBOOK,
    HEADPHONES,
    POWER_SUPPLY,
    PROCESSOR,
    CELL,
    TABLET,
    VIDEO_GAME_CONSOLE,
    USB_FLASH_DRIVE,
    PRINTER,
    TELEVISION,
    GAMING_CHAIR,
    MONITOR,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class SystemTi(StoreWithUrlExtensions):
    url_extensions = [
        ["pc-y-notebook", NOTEBOOK],
        ["perifericos", HEADPHONES],
        ["fuente-de-energia", POWER_SUPPLY],
        ["partes-y-componentes", PROCESSOR],
        ["telefonia", CELL],
        ["tablet-y-accesorios", TABLET],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["almacenamiento", USB_FLASH_DRIVE],
        ["impresoras-y-multifuncionales", PRINTER],
        ["smart-tv-y-audio", TELEVISION],
        ["sillas-y-escritorios", GAMING_CHAIR],
        ["monitores-y-proyectores", MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        product_urls = []
        session = session_with_proxy(extra_args)

        page = 1
        while True:
            if page > 20:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://www.systemti.cl/{}?page={}".format(
                url_extension, page
            )
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-block")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for product_container in product_containers:
                product_url = (
                    "https://www.systemti.cl" + product_container.find("a")["href"]
                )
                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        key = soup.find("meta", {"property": "og:id"})["content"]
        name = soup.find("h1", "page-header").text.strip()
        sku_tag = soup.find("span", "sku_elem")
        if sku_tag:
            sku = sku_tag.text.strip()
        else:
            sku = None

        picture_urls_tag = soup.find("div", "main-product-image")
        if picture_urls_tag:
            picture_urls = [picture_urls_tag.find("img")["src"]]
        else:
            picture_urls = None
        description = html_to_markdown(str(soup.find("div", "description")))
        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"]
        )
        part_number_match = re.search(r'"productID": "(.+)"', response.text)
        if part_number_match:
            part_number = part_number_match.groups()[0]
        else:
            part_number = None

        stock_tag_names = ["product-out-stock", "product-unavailable"]
        for stock_tag_name in stock_tag_names:
            stock_tag = soup.find("div", stock_tag_name)
            if "visible" in stock_tag.attrs["class"]:
                stock = 0
                break
        else:
            stock = -1

        if not price and not stock:
            return []

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
            description=description,
        )

        return [p]
