import re
from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.categories import (
    NOTEBOOK,
    RAM,
    CELL,
    TABLET,
    WEARABLE,
    ALL_IN_ONE,
    USB_FLASH_DRIVE,
    MEMORY_CARD,
    PROCESSOR,
    MOTHERBOARD,
    SOLID_STATE_DRIVE,
    STORAGE_DRIVE,
    VIDEO_CARD,
    COMPUTER_CASE,
    CPU_COOLER,
    POWER_SUPPLY,
    KEYBOARD,
    MOUSE,
    KEYBOARD_MOUSE_COMBO,
    HEADPHONES,
    STEREO_SYSTEM,
    MONITOR,
    TELEVISION,
    PRINTER,
    VIDEO_GAME_CONSOLE,
    GAMING_CHAIR,
    UPS,
    EXTERNAL_STORAGE_DRIVE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class MyShop(StoreWithUrlExtensions):
    url_extensions = [
        ["134", NOTEBOOK],  # portabilidad-notebooks
        ["40", NOTEBOOK],  # portabilidad-notebooks-notebooks-gamer
        ["145", NOTEBOOK],  # portabilidad-notebooks-notebooks-oficina
        ["146", NOTEBOOK],  # portabilidad-notebooks-notebooks
        ["147", NOTEBOOK],  # portabilidad-notebooks-notebooks-2-en-1
        ["119", NOTEBOOK],  # apple-macbook
        ["121", TABLET],  # apple-ipad
        ["124", HEADPHONES],  # apple-accesorios-apple
        ["66", CELL],  # celulares
        ["92", RAM],  # portabilidad-memorias-notebook
        ["21", TABLET],  # portabilidad-tablet
        ["56", WEARABLE],  # portabilidad-relojes
        ["20", ALL_IN_ONE],  # computacion-all-in-one
        ["32", MOTHERBOARD],  # partes-y-piezas-placas-madres
        ["35", RAM],  # partes-y-piezas-memorias-ram
        ["37", CPU_COOLER],  # partes-y-piezas-refrigeracion
        ["71", PROCESSOR],  # partes-y-piezas-procesadores
        ["73", KEYBOARD],  # partes-y-piezas-teclados
        ["105", MOUSE],  # partes-y-piezas-mouse
        ["110", KEYBOARD_MOUSE_COMBO],  # partes-y-piezas-combo-teclado-mouse
        ["33", VIDEO_CARD],  # partes-y-piezas-tarjetas-de-video
        ["36", COMPUTER_CASE],  # partes-y-piezas-gabinetes
        ["64", POWER_SUPPLY],  # partes-y-piezas-fuentes-de-poder
        ["72", STORAGE_DRIVE],  # almacenamiento-discos-hdd-internos
        ["108", SOLID_STATE_DRIVE],  # almacenamiento-discos-ssd-internos
        [
            "135",
            SOLID_STATE_DRIVE,
        ],  # almacenamiento-discos-ssd-internos-discos-ssd-sata-2-5-
        [
            "136",
            SOLID_STATE_DRIVE,
        ],  # almacenamiento-discos-ssd-internos-discos-ssd-m-2
        ["8", HEADPHONES],  # audio-video-audifonos-in-ear
        ["11", STEREO_SYSTEM],  # audio-video-parlantes
        ["14", HEADPHONES],  # audio-video-video-conferencia
        ["152", MONITOR],  # monitor-monitores
        ["139", MONITOR],  # monitor-monitores-monitores-gamer
        ["138", MONITOR],  # monitor-monitores-monitores-gamer
        ["9", HEADPHONES],  # audio-video-audifonos-on-ear
        ["140", TELEVISION],  # monitor-smart-tv
        ["27", PRINTER],  # impresion-impresion-laser
        ["30", PRINTER],  # impresion-otras-impresoras
        ["29", PRINTER],  # impresion-impresion-tinta
        ["10", HEADPHONES],  # gamer-audifonos-gamer
        ["42", GAMING_CHAIR],  # gamer-sillas-y-mesas
        ["41", VIDEO_GAME_CONSOLE],  # gamer-consolas
        ["75", KEYBOARD],  # gamer-teclados-gamer
        ["101", MOUSE],  # gamer-mouse-gamer
        ["85", UPS],  # empresas-ups
        ["117", NOTEBOOK],  # computacion-liquidacion
        [
            "69",
            EXTERNAL_STORAGE_DRIVE,
        ],  # almacenamiento-almacenamiento-externo
        [
            "154",
            EXTERNAL_STORAGE_DRIVE,
        ],  # computacion-almacenamiento-externo-ssd-externos
        [
            "153",
            EXTERNAL_STORAGE_DRIVE,
        ],  # computacion-almacenamiento-externo-discos-externos
        [
            "155",
            USB_FLASH_DRIVE,
        ],  # computacion-almacenamiento-externo-pendrives
        [
            "156",
            MEMORY_CARD,
        ],  # computacion-almacenamiento-externo-memoria-flash
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        print(url_extension)
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 20:
                raise Exception("Page overflow: " + url_extension)

            payload = {"tipo": "3", "page": str(page), "idFamilia": url_extension}
            res = session.post("https://www.myshop.cl/servicio/producto", json=payload)
            products_data = res.json()["resultado"]["items"]

            if not products_data:
                if page == 1:
                    raise Exception("Empty category: " + url_extension)
                break

            for product_entry in products_data:
                product_url = "https://www.myshop.cl" + product_entry["url"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        name = soup.find("h1").text.strip()
        product_data_tag = soup.find("div", "product_meta")
        sku = product_data_tag.findAll("p")[0].text.strip().split(": ")[1]
        part_number = product_data_tag.findAll("p")[3].text.strip().split(": ")[1]

        stock_containers = soup.find("div", "product_desc").findAll("li")
        stock = 0
        for stock_container in stock_containers:
            stock += int(re.search(r"(\d+)", stock_container.text).groups()[0])

        price_tags = soup.find("div", "product_d_right").findAll(
            "span", "current_price"
        )
        assert len(price_tags) == 2
        offer_price = Decimal(remove_words(price_tags[0].text))
        normal_price = Decimal(remove_words(price_tags[1].text))

        picture_urls = [
            x["data-image"] for x in soup.findAll("a", "elevatezoom-gallery")
        ]
        description = html_to_markdown(str(soup.find("div", "product_d_inner")))

        if "REACON" in name.upper():
            condition = "https://schema.org/RefurbishedCondition"
        else:
            condition = "https://schema.org/NewCondition"

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
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number,
            condition=condition,
        )
        return [p]
