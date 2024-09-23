import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    ALL_IN_ONE,
    GAMING_DESK,
    HEADPHONES,
    MOUSE,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    CPU_COOLER,
    PRINTER,
    STORAGE_DRIVE,
    SOLID_STATE_DRIVE,
    EXTERNAL_STORAGE_DRIVE,
    RAM,
    MOTHERBOARD,
    TELEVISION,
    UPS,
    VIDEO_CARD,
    COMPUTER_CASE,
    NOTEBOOK,
    MONITOR,
    STEREO_SYSTEM,
    GAMING_CHAIR,
    TABLET,
    VIDEO_GAME_CONSOLE,
    PROCESSOR,
    MEMORY_CARD,
    USB_FLASH_DRIVE,
    CELL,
    POWER_SUPPLY,
    WEARABLE,
    MICROPHONE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import cf_session_with_proxy, remove_words


class PcLinkStore(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos", HEADPHONES],
        ["disco-duro-externo", EXTERNAL_STORAGE_DRIVE],
        ["kit-teclado-y-mouse-2", KEYBOARD_MOUSE_COMBO],
        ["microfono", MICROPHONE],
        ["mouse", MOUSE],
        ["parlantes-subwoofer", STEREO_SYSTEM],
        ["teclado", KEYBOARD],
        ["smart-band", WEARABLE],
        ["smartphone", CELL],
        ["smartwatch", WEARABLE],
        ["unidad-de-estado-solido-ssd", SOLID_STATE_DRIVE],
        ["disco-duro-interno", STORAGE_DRIVE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["modulos-ram-propietarios", RAM],
        ["tarjetas-madre-placas-madre", MOTHERBOARD],
        ["procesador", PROCESSOR],
        ["tarjetas-de-video", VIDEO_CARD],
        ["ventiladores-y-sistemas-de-enfriamiento", CPU_COOLER],
        ["all-in-one", ALL_IN_ONE],
        ["apple-2", NOTEBOOK],
        ["notebook", NOTEBOOK],
        ["tableta", TABLET],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["impresoras-ink-jet", PRINTER],
        ["impresoras-laser", PRINTER],
        ["impresoras-multifuncionales", PRINTER],
        ["plotter", PRINTER],
        ["pendrive-unidades-flash-usb", USB_FLASH_DRIVE],
        ["tarjetas-de-memoria-flash", MEMORY_CARD],
        ["monitores-2", MONITOR],
        ["televisores", TELEVISION],
        ["ups-respaldo-de-energia", UPS],
        ["escritorios", GAMING_DESK],
        ["sillas-de-escritorio", GAMING_CHAIR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = cf_session_with_proxy(extra_args)
        session.headers["Content-Type"] = "application/x-www-form-urlencoded"
        session.headers["x-requested-with"] = "XMLHttpRequest"
        product_urls = []
        url_webpage = "https://www.pclinkstore.cl/categorias/{}" "".format(
            url_extension
        )
        print(url_webpage)
        data = session.get(url_webpage).text
        soup = BeautifulSoup(data, "html5lib")

        token = soup.find("meta", {"name": "csrf-token"})["content"]
        id_category = re.search('"id_category":(\\d+)', data).groups()[0]

        query_url = "https://www.pclinkstore.cl/productos"

        page = 1
        while True:
            if page > 50:
                raise Exception("Page overflow")

            query_params = {
                "_token": token,
                "id_category": id_category,
                "register": 48,
                "page": page,
            }

            product_data = session.post(query_url, query_params).text
            product_json = json.loads(product_data)["data"]
            product_soup = BeautifulSoup(product_json, "html5lib")

            product_containers = product_soup.findAll("div", "sv-producto-mod")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break

            for container in product_containers:
                if "Avisame" in container.text:
                    continue
                product_url = container.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = cf_session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html5lib")

        add_button = soup.find("button", "add-product-cart")

        if not add_button or "id" not in add_button.attrs:
            return []

        key = add_button["id"]
        name = soup.find("div", "product-name").text.strip()

        product_infos = soup.findAll("div", "product-info")
        price_infos = product_infos[0].findAll("div", "product-price-normal")
        if len(price_infos) == 0:
            price_infos = product_infos[0].findAll("div", "product-price-discount")
        if len(price_infos) == 1:
            normal_price = offer_price = Decimal(
                remove_words(price_infos[0].find("span").text)
            )
        else:
            offer_price = Decimal(remove_words(price_infos[0].find("span").text))
            normal_price = Decimal(remove_words(price_infos[1].find("span").text))
            if offer_price > normal_price:
                offer_price = normal_price

        sku_tag = product_infos[1].find("strong", text="Número de Parte:")
        sku = sku_tag.next.next.strip()
        stock_tags = product_infos[1].findAll("div", "justify-content-between")
        stock = 0
        for stock_tag in stock_tags:
            stock_text = stock_tag.find("strong").text.strip()
            if stock_text == "No disponible":
                continue
            stock += int(
                stock_text.replace("Unidades", "")
                .replace("Unidad", "")
                .replace(".", "")
            )

        condition_tag = product_infos[1].find("strong", text="Condición:")
        condition_text = condition_tag.next.next.strip()

        if "NUEVO" in condition_text:
            condition = "https://schema.org/NewCondition"
        else:
            condition = "https://schema.org/RefurbishedCondition"

        picture_urls = []
        picture_container = soup.find("ul", "slides")
        for a in picture_container.findAll("a"):
            picture_urls.append(a["href"])

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
            part_number=sku,
            condition=condition,
            picture_urls=picture_urls,
        )
        return [p]
