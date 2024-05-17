from decimal import Decimal

from bs4 import BeautifulSoup
from curl_cffi import requests

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown


class ElectronicaPanamericana(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only gets LG products

        # if not extra_args or "proxy" not in extra_args:
        #     raise Exception("BrightData Web Unlocker proxy arg is required")

        if category != TELEVISION:
            return []

        session = requests.Session(impersonate="chrome120")
        product_urls = []
        url = (
            "https://electronicapanamericana.com/marcas/lg/?"
            "product_count=1000&avia_extended_shop_select=yes"
        )
        print(url)
        response = session.get(url, verify=False, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        for container in soup.findAll("li", "product"):
            product_url = container.find("a")["href"]
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        # if not extra_args or "proxy" not in extra_args:
        #     raise Exception("BrightData Web Unlocker proxy arg is required")

        print(url)
        session = requests.Session(impersonate="chrome120")
        response = session.get(url, verify=False, timeout=30)
        soup = BeautifulSoup(response.text, "html5lib")

        sku = soup.find("span", "sku")

        if not sku:
            return []
        else:
            sku = sku.text.strip()

        name = "{} - {}".format(sku, soup.find("h1", "product_title").text.strip())[
            :255
        ]

        if soup.find("button", {"name": "add-to-cart"}):
            stock = -1
        else:
            stock = 0

        price_container = soup.find("span", "woocommerce-Price-amount")
        if not price_container:
            return []
        price = Decimal(price_container.text.replace("Q", "").replace(",", ""))

        picture_urls = [
            tag.find("a")["href"]
            for tag in soup.findAll("div", "woocommerce-product-gallery__image")
        ]
        description = html_to_markdown(
            str(soup.find("div", "woocommerce-Tabs-panel--description"))
        )

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            "GTQ",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
