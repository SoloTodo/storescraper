import logging
import re
from bs4 import BeautifulSoup
from decimal import Decimal
import validators

from storescraper.categories import (
    GAMING_CHAIR,
    ALL_IN_ONE,
    TELEVISION,
    CPU_COOLER,
    CASE_FAN,
    HEADPHONES,
    MOUSE,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    STEREO_SYSTEM,
    STORAGE_DRIVE,
    EXTERNAL_STORAGE_DRIVE,
    NOTEBOOK,
    MEMORY_CARD,
    USB_FLASH_DRIVE,
    RAM,
    TABLET,
    UPS,
    POWER_SUPPLY,
    COMPUTER_CASE,
    MOTHERBOARD,
    PROCESSOR,
    VIDEO_CARD,
    MONITOR,
    SOLID_STATE_DRIVE,
    PRINTER,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import remove_words, html_to_markdown, session_with_proxy


class PcExpress(StoreWithUrlExtensions):
    url_extensions = [
        ["321", HEADPHONES],  # Audifonos Gamers
        ["319", MOUSE],  # Mouse Gamers
        ["318", KEYBOARD],  # Teclados Gamers
        ["376", KEYBOARD_MOUSE_COMBO],  # Accesorios Gamer
        ["576", GAMING_CHAIR],  # Sillas gamer
        ["416", HEADPHONES],  # Audifonos
        ["427", STEREO_SYSTEM],  # Parlantes/Subwoofer/Soundbar
        ["101", STORAGE_DRIVE],  # Discos Duros para PC
        ["102", EXTERNAL_STORAGE_DRIVE],  # Discos Duros Externos
        ["284", MOUSE],  # Inalambricos
        ["131", KEYBOARD_MOUSE_COMBO],  # Kit Teclado y Mouse
        ["133", MOUSE],  # Mouse Gamers
        ["135", KEYBOARD],  # Teclados
        ["467", KEYBOARD_MOUSE_COMBO],  # Kit Teclado y Mouse
        ["471", MOUSE],  # Mouses
        ["136", NOTEBOOK],  # Notebooks Comercial y Corporativos
        ["477", ALL_IN_ONE],  # Equipos AIO
        ["479", NOTEBOOK],  # Notebooks Gamer
        ["106", MEMORY_CARD],  # Memorias Flash
        ["107", USB_FLASH_DRIVE],  # Pendrive
        ["126", RAM],  # Memorias para PC
        ["127", RAM],  # Memorias para Notebook
        ["225", TELEVISION],  # Televisores Smart TV
        ["269", TABLET],  # Tablets
        ["154", UPS],  # Ups
        ["461", POWER_SUPPLY],  # Fuentes de poder
        ["462", COMPUTER_CASE],  # Gabinetes
        ["472", MOTHERBOARD],  # Placas Madres
        ["473", PROCESSOR],  # Procesadores
        ["475", VIDEO_CARD],  # Tarjetas de Video
        ["523", MONITOR],  # Monitores
        ["413", STORAGE_DRIVE],  # Discos Duros
        ["331", SOLID_STATE_DRIVE],  # Unidades de estado Solido
        ["169", CPU_COOLER],  # Ventilacion para CPU
        ["170", CASE_FAN],  # Ventilacion para Gabinete
        ["493", PRINTER],  # Impresoras Hogar y Oficina
        ["282", HEADPHONES],  # Microfonos y Manos Libres
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
            "like Gecko) Chrome/66.0.3359.117 Safari/537.36"
        )

        category_url = (
            "https://tienda.pc-express.cl/index.php?route="
            "product/category&path=" + url_extension + "&page="
        )
        page = 1

        while True:
            if page > 15:
                raise Exception("Page overflow: " + url_extension)

            category_page_url = category_url + str(page)
            print(category_page_url)
            soup = BeautifulSoup(session.get(category_page_url).text, "html.parser")
            td_products = soup.findAll("div", "product-list__image")

            if len(td_products) == 0:
                if page == 1:
                    # raise Exception(category_page_url)
                    logging.warning("Empty category: " + url_extension)
                break

            else:
                for td_product in td_products:
                    original_product_url = td_product.find("a")["href"]

                    product_id = re.search(
                        r"product_id=(\d+)", original_product_url
                    ).groups()[0]

                    product_url = (
                        "https://tienda.pc-express.cl/"
                        "index.php?route=product/product&"
                        "product_id=" + product_id
                    )

                    product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
            "like Gecko) Chrome/66.0.3359.117 Safari/537.36"
        )
        soup = BeautifulSoup(session.get(url).text, "html.parser")

        if "¡No se encuentra el producto!" in soup.find("title").text:
            return []

        name = soup.find("h1", "rm-product-page__title").text[:250]
        sku = soup.find("div", "rm-product__id").h3.text
        if not soup.find("p", "rm-product__mpn"):
            part_number = None
        else:
            part_number = soup.find("p", "rm-product__mpn").text.split(":")[-1].strip()

        stock_container = soup.find("div", "rm-producto-stock-message")

        if not stock_container:
            stock = 0
        elif stock_container.text == "Sin disponibilidad para venta web":
            stock = 0
        else:
            stock = int(stock_container.text.split(" ")[0])

        offer_price = soup.find("div", "rm-product__price--cash").h3.text
        offer_price = Decimal(remove_words(offer_price))

        normal_price = soup.find("div", "rm-product__price--normal").h3.text
        normal_price = Decimal(remove_words(normal_price))

        description = html_to_markdown(str(soup.find("div", {"id": "tab-description"})))

        picture_urls = None

        thumbnails = soup.find("ul", "thumbnails")

        if thumbnails and validators.url(thumbnails.a["href"]):
            picture_urls = [thumbnails.a["href"]]

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
            picture_urls=picture_urls,
            part_number=part_number,
        )

        return [p]
