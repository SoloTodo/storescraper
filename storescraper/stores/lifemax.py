from decimal import Decimal
import json
import logging
import re

import validators
from bs4 import BeautifulSoup
from storescraper.categories import (
    COMPUTER_CASE,
    EXTERNAL_STORAGE_DRIVE,
    GAMING_CHAIR,
    HEADPHONES,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    MEMORY_CARD,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    NOTEBOOK,
    POWER_SUPPLY,
    PRINTER,
    PROCESSOR,
    RAM,
    SOLID_STATE_DRIVE,
    STEREO_SYSTEM,
    STORAGE_DRIVE,
    USB_FLASH_DRIVE,
    VIDEO_CARD,
    ALL_IN_ONE,
    CPU_COOLER,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown, remove_words


class Lifemax(StoreWithUrlExtensions):
    url_extensions = [
        ["notebooks", NOTEBOOK],
        ["impresoras-multifuncionales-tinta", PRINTER],
        ["Impresoras-de-Inyeccion-de-Tinta", PRINTER],
        ["all-in-one", ALL_IN_ONE],
        ["discos-ssd-unidad-estado-solido", SOLID_STATE_DRIVE],
        ["discos-duros-externos", EXTERNAL_STORAGE_DRIVE],
        ["discos-ssd-externos", EXTERNAL_STORAGE_DRIVE],
        ["disco-duro-interno", STORAGE_DRIVE],
        ["tarjeta-flash-micro-sd", MEMORY_CARD],
        ["pendrives", USB_FLASH_DRIVE],
        ["monitores", MONITOR],
        ["mouse", MOUSE],
        ["teclados", KEYBOARD],
        ["kits-de-mouse-y-teclado", KEYBOARD_MOUSE_COMBO],
        ["memoria-ram-notebook", RAM],
        ["memoria-ram-pc", RAM],
        ["refrigeracion-liquida", CPU_COOLER],
        ["fuentes-de-poder-pc", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["tarjetas-de-video", VIDEO_CARD],
        ["placas-madre", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["audifonos-gamer", HEADPHONES],
        ["sillas-gamer", GAMING_CHAIR],
        ["monitores-gamer", MONITOR],
        ["teclado-gamer", KEYBOARD],
        ["parlantes-gamer-1", STEREO_SYSTEM],
        ["mouse-y-teclados-gamer", MOUSE],
        ["memoria-ram-notebook-gamer", RAM],
        ["memoria-ram-pc-gaming", RAM],
        ["parlantes-portatiles", STEREO_SYSTEM],
        ["parlantes-y-subwoofers", STEREO_SYSTEM],
        ["barra-de-sonido", STEREO_SYSTEM],
        ["audifonos-in-ear", HEADPHONES],
        ["audifonos-on-ear-1", HEADPHONES],
        ["audifonos-over-ear", HEADPHONES],
        ["audifonos-tws", HEADPHONES],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)

            page_url = (
                f"https://www.lifemaxstore.cl/collections/{url_extension}?page={page}"
            )
            print(page_url)
            response = session.get(page_url)

            if response.url != page_url:
                raise Exception("Url mismatch: {} - {}".format(page_url, response.url))

            data = response.text
            soup = BeautifulSoup(data, "html5lib")
            product_container = soup.find("hdt-reval-items", "hdt-collection-products")

            if not product_container:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break

            product_containers = product_container.findAll(
                "hdt-card-product", "hdt-card-product"
            )

            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append("https://www.lifemaxstore.cl" + product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        products = []

        if response.url == "https://www.lifemaxstore.cl/":
            return []

        product_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[3].text
        )
        main_section = soup.find("div", "hdt-main-product")
        normal_price = Decimal(
            remove_words(
                main_section.find("hdt-price", "hdt-price")
                .find("span", "hdt-money")
                .text
            )
        )
        offer_price = Decimal(
            remove_words(
                main_section.find("p", "hdt-transferencia-price")
                .find("span", "hdt-money")
                .text
            )
        )
        picture_urls_container = main_section.find("div", "hdt-slider__viewport")

        if picture_urls_container:
            picture_urls = [
                f"https:{img['src'].split('?')[0]}"
                for img in picture_urls_container.findAll("img")
            ]
        else:
            picture_urls = [
                f"https:{soup.find('div', 'hdt-product__media').find('img')['src'].split('?')[0]}"
            ]
        description = html_to_markdown(
            soup.find("div", "hdt-product-tab__content").text
        )

        for variant in product_data["hasVariant"]:
            name = variant["name"]
            sku = variant["sku"]
            offer = variant["offers"]
            stock = -1 if offer["availability"] == "http://schema.org/InStock" else 0
            key = offer["url"].split("?variant=")[1]

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
                description=description,
            )

            products.append(p)

        return products
