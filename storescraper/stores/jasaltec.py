import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    EXTERNAL_STORAGE_DRIVE,
    TABLET,
    SOLID_STATE_DRIVE,
    POWER_SUPPLY,
    COMPUTER_CASE,
    RAM,
    MOTHERBOARD,
    PROCESSOR,
    VIDEO_CARD,
    CPU_COOLER,
    NOTEBOOK,
    MONITOR,
    HEADPHONES,
    MOUSE,
    STEREO_SYSTEM,
    KEYBOARD,
    UPS,
    VIDEO_GAME_CONSOLE,
    GAMING_CHAIR,
    GAMING_DESK,
    USB_FLASH_DRIVE,
    ALL_IN_ONE,
    STORAGE_DRIVE,
    MEMORY_CARD,
    KEYBOARD_MOUSE_COMBO,
    PRINTER,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Jasaltec(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            CPU_COOLER,
            NOTEBOOK,
            MONITOR,
            HEADPHONES,
            MOUSE,
            STEREO_SYSTEM,
            KEYBOARD,
            UPS,
            VIDEO_GAME_CONSOLE,
            GAMING_CHAIR,
            GAMING_DESK,
            TABLET,
            ALL_IN_ONE,
            STORAGE_DRIVE,
            MEMORY_CARD,
            KEYBOARD_MOUSE_COMBO,
            PRINTER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["disco-estado-solido-externo", EXTERNAL_STORAGE_DRIVE],
            ["disco-estado-solido-interno", SOLID_STATE_DRIVE],
            ["disco-mecanico-interno", STORAGE_DRIVE],
            ["disco-duro-externo", EXTERNAL_STORAGE_DRIVE],
            ["modulos-ram-notebook", RAM],
            ["modulos-ram-pc-escritorio", RAM],
            ["pendrive", USB_FLASH_DRIVE],
            ["tarjetas-de-memoria-flash", MEMORY_CARD],
            ["fuentes-de-poder", POWER_SUPPLY],
            ["gabinetes", COMPUTER_CASE],
            ["procesadores", PROCESSOR],
            ["tarjeta-madre", MOTHERBOARD],
            ["tarjetas-graficas", VIDEO_CARD],
            ["ventiladores-y-enfriadores", CPU_COOLER],
            ["all-in-one", ALL_IN_ONE],
            ["notebook", NOTEBOOK],
            ["notebook-gamer", NOTEBOOK],
            ["tablet", TABLET],
            ["combo-teclado-mouse", KEYBOARD_MOUSE_COMBO],
            ["combo-teclado-mouse-gamer", KEYBOARD_MOUSE_COMBO],
            ["audifonos-oficina", HEADPHONES],
            ["audifonos", HEADPHONES],
            ["mouse-oficina", MOUSE],
            ["mouses", MOUSE],
            ["teclados-oficina", KEYBOARD],
            ["teclados", KEYBOARD],
            ["parlantes", STEREO_SYSTEM],
            ["impresion-tinta", PRINTER],
            ["impresion-laser", PRINTER],
            ["impresoras-multifuncionales", PRINTER],
            ["monitores", MONITOR],
            ["ups", UPS],
            ["sillas", GAMING_CHAIR],
            ["sillas-oficina", GAMING_CHAIR],
            ["consola", VIDEO_GAME_CONSOLE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 15:
                    raise Exception("page overflow: " + url_extension)
                url_webpage = (
                    "https://jasaltec.cl/categoria-producto/{}/"
                    "page/{}/?_pjax=.main-page-wrapper"
                    "&per_page=36".format(url_extension, page)
                )
                print(url_webpage)
                response = session.get(url_webpage)

                if response.status_code == 404 and page == 1:
                    raise Exception(url_webpage)

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

        if "PAGE NOT FOUND" in soup.text:
            return []

        name = soup.find("h1", "product_title").text
        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[1]
        sku_tag = soup.find("span", "sku")

        if sku_tag:
            sku = soup.find("span", "sku").text.strip()
        else:
            sku = None

        if soup.find("p", "out-of-stock") or soup.find("p", "available-on-backorder"):
            stock = 0
        else:
            stock = -1

        if soup.find("p", "price").text == "":
            return []

        if soup.find("p", "price").find("ins"):
            offer_price = Decimal(
                remove_words(soup.find("p", "price").find("ins").text)
            )
        else:
            offer_price = Decimal(
                remove_words(soup.find("p", "price").find("bdi").text)
            )

        normal_price = (offer_price / Decimal("0.943")).quantize(0)
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
            normal_price,
            offer_price,
            "CLP",
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
        )
        return [p]
