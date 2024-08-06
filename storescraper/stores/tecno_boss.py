from decimal import Decimal
import logging
from bs4 import BeautifulSoup

from storescraper.categories import (
    HEADPHONES,
    MONITOR,
    MOUSE,
    RAM,
    SOLID_STATE_DRIVE,
    VIDEO_CARD,
    STEREO_SYSTEM,
    PRINTER,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import remove_words, session_with_proxy


class TecnoBoss(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos", HEADPHONES],
        ["smart-home", STEREO_SYSTEM],
        ["memorias-ram", RAM],
        ["ssd", SOLID_STATE_DRIVE],
        ["home-office", MONITOR],
        ["tarjetas-de-video", VIDEO_CARD],
        ["mouse-y-teclados", MOUSE],
        ["computadores", MONITOR],
        ["impresoras", PRINTER],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://www.tecnoboss.cl/{}" "?page={}".format(
                url_extension, page
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("div", "product-block")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a", "product-image")["href"]
                product_urls.append("https://www.tecnoboss.cl" + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("form", {"name": "buy"})["action"].split("/")[-1]

        name = soup.find("meta", {"property": "og:title"})["content"]
        description = soup.find("meta", {"property": "og:description"})["content"]

        price = Decimal(remove_words(soup.find("span", "product-form-price").text))

        if not price:
            return []

        sku_span = soup.find("span", "sku_elem")
        if sku_span and sku_span.text != "":
            sku = sku_span.text
        else:
            sku = None

        stock_div = soup.find("div", "product-page_stock")
        if stock_div:
            stock = int(stock_div.find("span").text)
        else:
            stock = 0

        picture_urls = []
        picture_container = soup.find("div", "carousel-inner")
        if picture_container:
            for image in picture_container.findAll("img"):
                picture_urls.append(image["src"])
        else:
            image = soup.find("div", "main-product-image").find("img")
            picture_urls.append(image["src"])

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
