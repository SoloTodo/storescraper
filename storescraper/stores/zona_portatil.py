import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    ALL_IN_ONE,
    NOTEBOOK,
    HEADPHONES,
    VIDEO_GAME_CONSOLE,
    GAMING_CHAIR,
    COMPUTER_CASE,
    RAM,
    MOTHERBOARD,
    PROCESSOR,
    VIDEO_CARD,
    STORAGE_DRIVE,
    SOLID_STATE_DRIVE,
    EXTERNAL_STORAGE_DRIVE,
    MEMORY_CARD,
    MONITOR,
    PRINTER,
    CPU_COOLER,
    POWER_SUPPLY,
    KEYBOARD_MOUSE_COMBO,
    CASE_FAN,
    UPS,
    MOUSE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class ZonaPortatil(StoreWithUrlExtensions):
    url_extensions = [
        ["teclado-mouse", KEYBOARD_MOUSE_COMBO],
        ["fuente-de-poder", POWER_SUPPLY],
        ["memoria-notebook", RAM],
        ["memoria-pc", RAM],
        ["placa-madre", MOTHERBOARD],
        ["procesador", PROCESSOR],
        ["tarjeta-de-video", VIDEO_CARD],
        ["ventilador", CASE_FAN],
        ["disco-duro-externo", EXTERNAL_STORAGE_DRIVE],
        ["disco-duro-servidor", STORAGE_DRIVE],
        ["disco-duro-ssd", SOLID_STATE_DRIVE],
        ["memorias-flash", MEMORY_CARD],
        ["aio-todo-en-uno", ALL_IN_ONE],
        ["notebook", NOTEBOOK],
        ["ups", UPS],
        ["impresoras", PRINTER],
        ["monitores-monitores", MONITOR],
        ["impresoras-open-box", PRINTER],
        ["notebook-partes-y-piezas-open-box", NOTEBOOK],
        ["memoria-notebook-partes-y-piezas-open-box", RAM],
        ["memoria-pc-partes-y-piezas-open-box", RAM],
        ["notebook-computadores-open-box", RAM],
        ["disco-duro-externo-almacenamiento-open-box", EXTERNAL_STORAGE_DRIVE],
        ["disco-duro-ssd-almacenamiento-open-box", SOLID_STATE_DRIVE],
        ["ups-y-energia-ups-y-energia-ups-y-energia", UPS],
        ["mouse", MOUSE],
        ["teclado-mouse-accesorios-zona-gamer", KEYBOARD_MOUSE_COMBO],
        ["silla-gamer", GAMING_CHAIR],
        ["ventilador-accesorios-zona-gamer", CPU_COOLER],
        ["gabinetes-gabinetes", COMPUTER_CASE],
        ["monitores-monitores-zona-gamer", MONITOR],
        ["refrigeracion-refrigeracion", CPU_COOLER],
        ["audifonos-audio-zona-gamer", HEADPHONES],
        ["audifonos-audifonos", HEADPHONES],
        ["memorias-notebook-memorias-notebook", RAM],
        ["tarjetas-graficas-tarjetas-graficas", VIDEO_CARD],
        ["tarjeta-de-video-partes-y-piezas-zona-gamer", VIDEO_CARD],
        ["placa-madre-partes-y-piezas-zona-gamer", MOTHERBOARD],
        ["consolas-consolas", VIDEO_GAME_CONSOLE],
        ["memorias-pc-memorias-pc", RAM],
        ["placas-madres-placas-madres", MOTHERBOARD],
        ["fuente-de-poder-fuente-de-poder-zona-gamer", POWER_SUPPLY],
        ["procesadores-procesadores", PROCESSOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)

            url_webpage = "https://zonaportatil.cl/categoria/{}/page/{}/".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "html.parser")
            product_containers = soup.findAll("article", "product")

            if not product_containers:
                if page == 1:
                    logging.warning("Empty category")
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
        name = soup.find("p", "product_title").text.strip()
        alternate_url = soup.find(
            "link", {"rel": "alternate", "type": "application/json"}
        )["href"]
        key_match = re.search("/product/(\d+)", alternate_url)
        key = key_match.groups()[0]

        qty_input = soup.find("input", "input-text qty text")
        if qty_input:
            if qty_input["max"]:
                stock = int(qty_input["max"])
            else:
                stock = -1
        else:
            if soup.find("button", "single_add_to_cart_button"):
                stock = 1
            else:
                stock = 0

        price_containers = soup.find("p", "price")
        normal_price = Decimal(
            remove_words(price_containers.find("span", "woocommerce-Price-amount").text)
        )

        offer_price_tag = price_containers.find("p", "price-transferencia")

        if not offer_price_tag:
            raise Exception(response.text)

        offer_price = Decimal(remove_words(offer_price_tag.find("bdi").text))
        sku = re.search(r"Part Number: (.+?)<", response.text).groups()[0]
        picture_urls = [
            x["href"]
            for x in soup.find("div", "woocommerce-product-gallery__wrapper").findAll(
                "a"
            )
        ]

        if "OPEN" in name.upper():
            condition = "https://schema.org/OpenBoxCondition"
        else:
            condition = "https://schema.org/NewCondition"

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
            condition=condition,
        )
        return [p]
