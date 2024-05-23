from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import *
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class VyTComputacion(StoreWithUrlExtensions):
    url_extensions = [
        ["impresoras", PRINTER],
        ["pendrive-de-almacenamiento", USB_FLASH_DRIVE],
        ["memorias-sd-de-camaras-drone-gopro", MEMORY_CARD],
        ["ssd-disk", SOLID_STATE_DRIVE],
        ["discos-internos-y-externos", STORAGE_DRIVE],
        ["fans-ventilador", CASE_FAN],
        ["placa-madre", MOTHERBOARD],
        ["fuente-de-poder", POWER_SUPPLY],
        ["refrigeracion-liquida", CPU_COOLER],
        ["procesadores", PROCESSOR],
        ["tarjetas-graficas", VIDEO_CARD],
        ["memorias-ram", RAM],
        ["sillas-gamer", GAMING_CHAIR],
        ["teclados-para-pc", KEYBOARD],
        ["parlantes", STEREO_SYSTEM],
        ["audifonos", HEADPHONES],
        ["monitores-y-pantallas-para-pc", MONITOR],
        ["gabinetes-para-pc", COMPUTER_CASE],
        ["audio", STEREO_SYSTEM],
        ["ups", UPS],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = (
                "https://www.vytcomputacion.cl/categoria-producto/{}/page/{}/".format(
                    url_extension, page
                )
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "html.parser")
            product_containers = soup.findAll("li", "product")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
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
        soup = BeautifulSoup(response.text, "html.parser")
        name = soup.find("h4", "product_title").text.strip()
        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[-1]
        stock = -1 if soup.find("button", "single_add_to_cart_button") else 0
        price_tags = soup.find("p", "price").findAll("span", "woocommerce-Price-amount")
        if not price_tags:
            return []
        price = Decimal(remove_words(price_tags[-1].text.strip()))
        sku_tag = soup.find("span", "sku")
        if sku_tag:
            sku = sku_tag.text.strip()
        else:
            sku = None
        picture_urls = [soup.find("meta", {"property": "og:image"})["content"]]

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
        )
        return [p]
