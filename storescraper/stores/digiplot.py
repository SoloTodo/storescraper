import json
import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    ALL_IN_ONE,
    COMPUTER_CASE,
    EXTERNAL_STORAGE_DRIVE,
    GAMING_CHAIR,
    CPU_COOLER,
    CASE_FAN,
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
    TELEVISION,
    UPS,
    USB_FLASH_DRIVE,
    VIDEO_CARD,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, session_with_proxy


class Digiplot(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            HEADPHONES,
            STEREO_SYSTEM,
            POWER_SUPPLY,
            COMPUTER_CASE,
            PRINTER,
            RAM,
            MONITOR,
            NOTEBOOK,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            UPS,
            VIDEO_CARD,
            GAMING_CHAIR,
            CASE_FAN,
            MEMORY_CARD,
            ALL_IN_ONE,
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["almacenamiento/disco-duro-externo-%28sata%29", EXTERNAL_STORAGE_DRIVE],
            ["almacenamiento/disco-duro-externo-%28ssd%29", EXTERNAL_STORAGE_DRIVE],
            ["almacenamiento/disco-duro-notebook", STORAGE_DRIVE],
            ["almacenamiento/disco-duro-pc", STORAGE_DRIVE],
            ['almacenamiento/disco-ssd-2,5"', SOLID_STATE_DRIVE],
            ["almacenamiento/disco-ssd-m.2", SOLID_STATE_DRIVE],
            ["almacenamiento/memoria-flash-sd-microsd", MEMORY_CARD],
            ["almacenamiento/pendrive", USB_FLASH_DRIVE],
            ["audio/audifono-alambrico", HEADPHONES],
            ["audio/audifono-bluetooth", HEADPHONES],
            ["audio/parlantes-1.1", STEREO_SYSTEM],
            ["audio/parlantes-2.0", STEREO_SYSTEM],
            ["computador-escritorio/all-in-one", ALL_IN_ONE],
            ["gabinetes-y-fuentes/fuente-poder", POWER_SUPPLY],
            ["gabinetes-y-fuentes/fuente-poder-gamer", POWER_SUPPLY],
            ["gabinetes-y-fuentes/gabinete-gamer", COMPUTER_CASE],
            ["gabinetes-y-fuentes/gabinete-slim", COMPUTER_CASE],
            ["gabinetes-y-fuentes/gabinete-vertical", COMPUTER_CASE],
            ["gabinetes-y-fuentes/ventilador-gabinete", CASE_FAN],
            ["impresoras/laser", PRINTER],
            ["impresoras/multifuncion-laser", PRINTER],
            ["impresoras/multifuncion-tinta", PRINTER],
            ["memorias/memoria-gamer-y-grafica", RAM],
            ["memorias/memoria-notebook-%28sodimm%29", RAM],
            ["memorias/memoria-pc-%28udimm%29", RAM],
            ["monitor-y-televisor/monitor-gamer", MONITOR],
            ["monitor-y-televisor/monitor-led", MONITOR],
            ["monitor-y-televisor/monitor-segunda-seleccion", MONITOR],
            ["monitor-y-televisor/televisor-led", TELEVISION],
            ["notebook-y-tablet", NOTEBOOK],
            ["placa-madre", MOTHERBOARD],
            ["procesadores", PROCESSOR],
            ["procesadores/ventilador-cpu", CPU_COOLER],
            ["teclado-y-mouse/mouse-alambrico", MOUSE],
            ["teclado-y-mouse/mouse-bluetooth", MOUSE],
            ["teclado-y-mouse/mouse-gamer", MOUSE],
            ["teclado-y-mouse/mouse-inalambrico", MOUSE],
            ["teclado-y-mouse/teclado", KEYBOARD],
            ["teclado-y-mouse/teclado-y-mouse", KEYBOARD_MOUSE_COMBO],
            ["ups-y-alargador-elec/ups-hasta-900va", UPS],
            ["ups-y-alargador-elec/ups-sobre-1000va", UPS],
            ["video/tarjetas-video", VIDEO_CARD],
            ["sillas/sillas-gamer", GAMING_CHAIR],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 10:
                    raise Exception("Page Overflow")

                if "/" in url_extension:
                    cat = "categorys"
                else:
                    cat = "category"

                url = "https://www.digiplot.cl/product/{}/{}?page={}".format(
                    cat, url_extension, page
                )

                data = session.get(url).text
                soup = BeautifulSoup(data, "lxml")
                product_containers = soup.findAll("div", "single-product")

                if not product_containers:
                    if page == 1:
                        logging.warning("Empty category: {}".format(url_extension))
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
        response = session.get(url, verify=False)

        soup = BeautifulSoup(response.text, "lxml")
        data = (
            re.search(r"value_product = ([\s\S]+?)\];", response.text).groups()[0] + "]"
        )
        data = json.loads(data)[0]

        name = data["descripcion"].strip()
        sku = data["idproducto"].strip()

        stock = 0
        stock_containers = soup.findAll("div", "product-single__availability-item")
        for container in stock_containers:
            stock_text = container.text.split(":")[1].split("unid")[0].strip()
            if "Mas de" in stock_text:
                stock = -1
                break
            elif stock_text != "":
                stock += int(remove_words(stock_text))

        offer_price = Decimal(data["precioweb1"])
        normal_price = Decimal(data["precioweb2"])

        if offer_price > normal_price:
            return []

        description = None
        if data["long_descrip"]:
            description = html_to_markdown(data["long_descrip"])
        picture_urls = [x["href"] for x in soup.findAll("a", "fancybox")]

        condition_span = soup.find("p", {"id": "product_condition"}).find(
            "span", "editable"
        )
        if "nuevo" in condition_span.text.lower():
            condition = "https://schema.org/NewCondition"
        else:
            condition = "https://schema.org/RefurbishedCondition"

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
            description=description,
            condition=condition,
            picture_urls=picture_urls,
        )

        return [p]
