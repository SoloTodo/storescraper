import logging
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    GAMING_CHAIR,
    MICROPHONE,
    CPU_COOLER,
    NOTEBOOK,
    VIDEO_CARD,
    PROCESSOR,
    MONITOR,
    MOTHERBOARD,
    RAM,
    STORAGE_DRIVE,
    SOLID_STATE_DRIVE,
    POWER_SUPPLY,
    COMPUTER_CASE,
    TABLET,
    EXTERNAL_STORAGE_DRIVE,
    MOUSE,
    USB_FLASH_DRIVE,
    ALL_IN_ONE,
    HEADPHONES,
    PRINTER,
    PROJECTOR,
    TELEVISION,
    CELL,
    MEMORY_CARD,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    STEREO_SYSTEM,
    VIDEO_GAME_CONSOLE,
    UPS,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import remove_words, html_to_markdown, session_with_proxy


class Wei(StoreWithUrlExtensions):
    url_extensions = [
        ["752", TABLET],  # Tablets
        ["678", TABLET],  # TABLETS
        ["1267", NOTEBOOK],  # Notebooks
        ["731", NOTEBOOK],  # NOTEBOOK GAMER
        ["755", NOTEBOOK],  # MACBOOK
        ["1252", MOUSE],  # Mouse
        ["807", MOUSE],  # MOUSE GAMER
        ["1138", EXTERNAL_STORAGE_DRIVE],  # Discos externos
        ["515", SOLID_STATE_DRIVE],  # SSD
        ["1142", USB_FLASH_DRIVE],  # Pendrive
        ["511", STORAGE_DRIVE],  # DISCOS DUROS INTERNOS
        ["769", ALL_IN_ONE],  # ALL IN ONE - AIO
        ["770", HEADPHONES],  # AUDIFONOS CON MICROFONO
        ["1176", HEADPHONES],  # AUDíFONOS
        ["805", HEADPHONES],  # AUDIFONOS GAMER
        ["1126", MOTHERBOARD],  # PLACAS MADRES
        ["730", MOTHERBOARD],  # PLACAS GAMER
        ["1219", COMPUTER_CASE],  # GABINETES
        ["729", COMPUTER_CASE],  # GABINETES GAMER
        ["1222", POWER_SUPPLY],  # FUENTES DE PODER (PSU)
        ["1305", VIDEO_CARD],  # TARJETAS DE VIDEO
        ["811", VIDEO_CARD],  # TARJETAS GRAFICAS GAMER
        ["1117", PROCESSOR],  # Procesadores
        ["1238", RAM],  # MEMORIAS
        ["1240", RAM],  # MEMORIA PC GAMER
        ["1162", CPU_COOLER],  # VENTILADORES / FAN
        ["804", CPU_COOLER],  # REFRIGERACION E ILUMINACION
        ["784", PRINTER],  # IMPRESORA TINTA
        ["773", PRINTER],  # IMPRESORAS LASER
        ["775", PRINTER],  # IMPRESORAS MULTIFUNCIONALES
        ["1226", PRINTER],  # IMPRESORAS TINTA
        ["1249", PROJECTOR],  # PROYECTORES
        ["1245", MONITOR],  # MONITORES LED, LCD, TFT
        ["810", MONITOR],  # MONITORES GAMER
        ["1248", TELEVISION],  # TELEVISORES
        ["1295", CELL],  # SMARTPHONES
        ["1141", MEMORY_CARD],  # Tarjetas de memoria
        ["806", KEYBOARD],  # TECLADOS GAMER
        ["1254", KEYBOARD],  # TECLADOS (PS2, USB, NUMERICOS)
        ["1253", KEYBOARD_MOUSE_COMBO],  # COMBOS TECLADO / MOUSE
        ["808", KEYBOARD_MOUSE_COMBO],  # KIT TECLADO Y MOUSE GAMER
        ["1175", STEREO_SYSTEM],  # PARLANTES
        ["793", STEREO_SYSTEM],  # AMPLIFICADORES
        ["1209", VIDEO_GAME_CONSOLE],  # CONSOLAS JUEGOS Y CONTROLES
        ["782", UPS],  # UPS
        ["809", GAMING_CHAIR],
        ["1182", MICROPHONE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.3"
        )

        product_urls = []
        page = 0
        local_urls = []
        done = False

        while not done:
            if page >= 10:
                raise Exception("Page overflow: " + url_extension)

            page_url = "https://www.wei.cl/categoria/{}?page={}" "".format(
                url_extension, page
            )
            print(page_url)
            res = session.get(page_url)
            soup = BeautifulSoup(res.text, "html.parser")

            product_cells = soup.findAll("div", "box-producto")

            if not product_cells:
                if page == 0:
                    logging.warning("Empty category: {}".format(url_extension))
                break

            for cell in product_cells:
                product_url = cell.find("a")["href"]
                if product_url in local_urls:
                    done = True
                    break
                local_urls.append(product_url)

            page += 1

        product_urls.extend(local_urls)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )

        try:
            page_source = session.get(url, timeout=61).text
        except Exception:
            return []
        sku = re.search(r"productoPrint\('(.+)'\);", page_source)

        if not sku:
            return []

        sku = sku.groups()[0]
        soup = BeautifulSoup(page_source, "html.parser")

        name = soup.find("meta", {"name": "description"})["content"]

        stock_div = soup.find("div", "col-55 col-100-md-2 pb20")
        if (
            "IMPORTACION" in name
            or "en tránsito" in stock_div.text.lower()
            or "agotado" in stock_div.text.lower()
        ):
            stock = 0
        else:
            stock = -1

        pricing_container = soup.find("div", "col-50 col-100-sm-1").findAll(
            "div", style=lambda value: value and "bolder" in value
        )

        if len(pricing_container) == 0:
            return []

        offer_price = Decimal(
            remove_words(re.search(r"\$[0-9.]*", pricing_container[0].text).group(0))
        )
        normal_price = Decimal(
            remove_words(re.search(r"\$[0-9.]*", pricing_container[2].text).group(0))
        )

        assert normal_price

        if "reacondicionado" in name.lower():
            condition = "https://schema.org/RefurbishedCondition"
        else:
            condition = "https://schema.org/NewCondition"

        description = html_to_markdown(str(soup.find("div", {"id": "tab-producto"})))

        if normal_price < offer_price:
            offer_price = normal_price

        picture_urls = []
        for picture_container in soup.findAll("div", "slider-item"):
            picture_url = picture_container.find("img")["src"].replace(" ", "%20")
            picture_urls.append(picture_url)

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
            condition=condition,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
