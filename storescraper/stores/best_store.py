import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import (
    POWER_SUPPLY,
    PROCESSOR,
    MOTHERBOARD,
    VIDEO_CARD,
    CPU_COOLER,
    NOTEBOOK,
    TABLET,
    ALL_IN_ONE,
    RAM,
    USB_FLASH_DRIVE,
    MEMORY_CARD,
    MONITOR,
    TELEVISION,
    HEADPHONES,
    KEYBOARD_MOUSE_COMBO,
    STEREO_SYSTEM,
    COMPUTER_CASE,
    CELL,
    EXTERNAL_STORAGE_DRIVE,
    UPS,
    GAMING_CHAIR,
    WEARABLE,
    PRINTER,
    AIR_CONDITIONER,
    SOLID_STATE_DRIVE,
    VIDEO_GAME_CONSOLE,
    STORAGE_DRIVE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class BestStore(StoreWithUrlExtensions):
    url_extensions = [
        ["109-componentes-informaticos-fuentes-de-poder", POWER_SUPPLY],
        ["106-componentes-informaticos-cajas-gabinetes", COMPUTER_CASE],
        ["275-componentes-informaticos-procesadores", PROCESSOR],
        ["180-componentes-informaticos-tarjetas-madre-placas-madre", MOTHERBOARD],
        ["181-componentes-informaticos-tarjetas-de-video", VIDEO_CARD],
        [
            "115-componentes-informaticos-ventiladores-y-sistemas-de-enfriamiento",
            CPU_COOLER,
        ],
        ["230-computadores?q=Tipo-Notebook", NOTEBOOK],
        ["230-computadores?q=Tipo-Tablet", TABLET],
        ["230-computadores?q=Tipo-All+in+One", ALL_IN_ONE],
        ["172-memorias", RAM],
        ["122-almacenamiento?q=Tipo-Memorias+SD+y+Micro+Sd", MEMORY_CARD],
        ["122-almacenamiento?q=Tipo-Pendrive", USB_FLASH_DRIVE],
        ["152-monitores-monitores", MONITOR],
        ["233-monitores-televisores", TELEVISION],
        ["117-auriculares-y-manos-libres", HEADPHONES],
        ["112-perifericos-combos-de-teclado-y-raton", KEYBOARD_MOUSE_COMBO],
        ["160-perifericos-parlantes-bocinas-cornetas", STEREO_SYSTEM],
        ["1097-monitores-gamer", MONITOR],
        ["1098-notebook-gamer", NOTEBOOK],
        ["1101-gabinetes-gamer", COMPUTER_CASE],
        ["1102-auriculares-gamer", HEADPHONES],
        ["1120-sillas-gamer", GAMING_CHAIR],
        ["228-celulares-celulares-desbloqueados", CELL],
        ["122-almacenamiento?q=Tipo-Discos+Duros+Externos", EXTERNAL_STORAGE_DRIVE],
        ["122-almacenamiento?q=Tipo+de+Disco+Duro-SSD", SOLID_STATE_DRIVE],
        ["122-almacenamiento?q=Tipo+de+Disco+Duro-HDD-Unidad+Híbrida", STORAGE_DRIVE],
        ["127-proteccion-de-poder-ups-respaldo-de-energia", UPS],
        ["1099-accesorios-gamer", GAMING_CHAIR],
        ["226-tecnologia-portatil-relojes", WEARABLE],
        ["143-impresoras-y-escaneres-impresoras-ink-jet", PRINTER],
        ["174-impresoras-y-escaneres-impresoras-laser", PRINTER],
        ["144-impresoras-y-escaneres-impresoras-multifuncionales", PRINTER],
        ["1028-plotters", PRINTER],
        ["254-climatizacion", AIR_CONDITIONER],
        ["302-videojuegos-consolas", VIDEO_GAME_CONSOLE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 50:
                raise Exception("page overflow: " + url_extension)
            if "?" in url_extension:
                separator = "&"
            else:
                separator = "?"

            url_webpage = "https://www.beststore.cl/{}{}page={}".format(
                url_extension, separator, page
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html.parser")
            product_containers = soup.find("div", {"id": "js-product-list"}).findAll(
                "article", "product-miniature"
            )
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

        if response.status_code == 404 or response.url != url:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.find("div", "product-container")
        key = container.find("meta", {"itemprop": "sku"})["content"]
        name = container.find("h1", {"itemprop": "name"}).text

        part_number_tag = container.find("label", text="PN: ")
        if part_number_tag:
            part_number = part_number_tag.parent.find("span").text.strip()
        else:
            part_number = None

        sku_tag = container.find("div", "product-reference")

        if sku_tag:
            sku = sku_tag.find("span").text.strip()
        else:
            sku = None

        add_to_cart_button = soup.find("button", "btn btn-primary add-to-cart")

        if "disabled" in add_to_cart_button.attrs:
            stock = 0
        else:
            stock_tag = container.find("label", text="Stock: ")
            if stock_tag:
                stock_text = stock_tag.parent.find("span").text
                if stock_text.strip() == "Consultar stock":
                    stock = 0
                else:
                    stock = int(stock_text)
                    if stock < 4:
                        stock = 0
            else:
                stock = 0

        normal_price = Decimal(
            remove_words(soup.find("div", "current-price").find("span").text)
        )
        offer_price = Decimal(
            soup.find("div", "current-price-money")
            .find("span")
            .text.replace("$\xa0", "")
            .replace(".", "")
        )
        picture_url = [
            tag["src"]
            for tag in soup.find("div", "images-container").findAll("img")
            if validators.url(tag["src"])
        ]

        condition_tag = soup.find("div", "product-condition")
        condition_text = condition_tag.find("span").text.strip()
        if condition_text.upper() == "NUEVO":
            condition = "https://schema.org/NewCondition"
        elif condition_text.upper() == "UTILIZADO":
            condition = "https://schema.org/UsedCondition"
        elif condition_text.upper() == "CAJA ABIERTA":
            condition = "https://schema.org/OpenBoxCondition"
        elif condition_text.upper() == "CAJA DAÑADA":
            condition = "https://schema.org/OpenBoxCondition"
        elif condition_text.upper() == "REFACCIONADO":
            condition = "https://schema.org/RefurbishedCondition"
        else:
            raise Exception("Invalid condition: " + condition_text)

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
            part_number=part_number,
            picture_urls=picture_url,
            condition=condition,
        )
        return [p]
