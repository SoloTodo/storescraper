from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import *
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Tekmachine(StoreWithUrlExtensions):
    url_extensions = [
        ["procesadores", PROCESSOR],
        ["placas-madres", MOTHERBOARD],
        ["memorias", RAM],
        ["discos-solidos", SOLID_STATE_DRIVE],
        ["tarjetas-de-video", VIDEO_CARD],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["audifonos", HEADPHONES],
        ["mouse", MOUSE],
        ["teclado", KEYBOARD],
        ["case-fan", CASE_FAN],
        ["cpu-cooling", CPU_COOLER],
        ["monitores", MONITOR],
        ["sistema-de-sonido", STEREO_SYSTEM],
        ["sillas-gamers", GAMING_CHAIR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 15:
                raise Exception("page overflow: " + url_extension)
            url_webpage = (
                "https://tekmachine.cl/product-category/{}/page/{}/"
                "?_pjax=.main-page-wrapper"
            ).format(url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-grid-item")

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
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", "product_title").text.strip()
        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[1]
        sku_tag = soup.find("span", "sku")

        if sku_tag:
            sku = soup.find("span", "sku").text.strip()[:45]
        else:
            sku = None

        if soup.find("p", "out-of-stock") or soup.find("p", "available-on-backorder"):
            stock = 0
        else:
            stock = -1

        price = Decimal(remove_words(soup.find("p", "price").findAll("bdi")[1].text))

        picture_urls = [
            tag["src"]
            for tag in soup.find("div", "woocommerce-product" "-gallery").findAll("img")
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
            picture_urls=picture_urls,
        )
        return [p]
