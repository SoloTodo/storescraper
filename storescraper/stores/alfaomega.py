import json

from bs4 import BeautifulSoup
from decimal import Decimal
import re
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import (
    PROCESSOR,
    MOTHERBOARD,
    VIDEO_CARD,
    POWER_SUPPLY,
    SOLID_STATE_DRIVE,
    COMPUTER_CASE,
    RAM,
    CPU_COOLER,
    NOTEBOOK,
    USB_FLASH_DRIVE,
    PRINTER,
    MONITOR,
    KEYBOARD,
    MOUSE,
)


class Alfaomega(StoreWithUrlExtensions):
    url_extensions = [
        ["procesadores-intel-2", PROCESSOR],
        ["procesadores-amd-2", PROCESSOR],
        ["mouse-y-teclados", MOUSE],
        ["refrigeracion", CPU_COOLER],
        ["placas-intel-2", MOTHERBOARD],
        ["placas-amd-2", MOTHERBOARD],
        ["memorias", RAM],
        ["discos-ssd", SOLID_STATE_DRIVE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["tarjetas-graficas", VIDEO_CARD],
        ["monitores", MONITOR],
        ["mouse-y-teclados", KEYBOARD],
        ["pendrive", USB_FLASH_DRIVE],
        ["notebooks", NOTEBOOK],
        ["impresoras-y-suministros", PRINTER],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        page = 1

        while True:
            url = "https://aopc.cl/categoria-producto/{}/page/{}".format(
                url_extension, page
            )
            print(url)
            response = session.get(url)

            if response.status_code == 404:
                if page == 1:
                    raise Exception("Invalid section: " + url)
                break

            soup = BeautifulSoup(response.text, "lxml")
            products = soup.findAll("li", "product")

            if not products:
                break

            for product in products:
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        soup = BeautifulSoup(session.get(url).text, "lxml")

        name = soup.find("h4", "product_title").text
        sku_container = soup.find("span", "sku")
        sku = sku_container.text.strip() if sku_container else None

        if not sku:
            return []

        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
        description = html_to_markdown(str(soup.find("div", "description")))
        stock_container = soup.find("span", "stock in-stock")
        stock = (
            int(re.search(r"\d+", stock_container.text).group())
            if stock_container
            else 0
        )
        price_container = soup.find(
            "div", "elementor-product-price-block-yes"
        ).find_all("span", "woocommerce-Price-amount amount")
        normal_price = Decimal(
            price_container[0].text.replace("$", "").replace(".", "")
        )
        offer_price = Decimal(price_container[1].text.replace("$", "").replace(".", ""))
        gallery = soup.find("div", "woocommerce-product-gallery__wrapper").find_all("a")
        picture_urls = [img["href"] for img in gallery]

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
            sku=key,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
