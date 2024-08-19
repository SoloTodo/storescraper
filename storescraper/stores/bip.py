import logging
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    GAMING_CHAIR,
    CPU_COOLER,
    CELL,
    NOTEBOOK,
    ALL_IN_ONE,
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
    USB_FLASH_DRIVE,
    MEMORY_CARD,
    MOUSE,
    PRINTER,
    KEYBOARD,
    HEADPHONES,
    STEREO_SYSTEM,
    UPS,
    TELEVISION,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy


class Bip(StoreWithUrlExtensions):
    url_extensions = [
        ["166", NOTEBOOK],  # Notebooks
        ["218", ALL_IN_ONE],  # All in One
        ["792", VIDEO_CARD],  # Tarjetas de video
        ["784", PROCESSOR],  # Procesadores
        ["761", MONITOR],  # Monitores
        ["785", MOTHERBOARD],  # Placas madre
        ["132", RAM],  # RAM PC
        ["178", RAM],  # RAM Notebook
        ["125", STORAGE_DRIVE],  # Disco Duro 2,5'
        ["124", STORAGE_DRIVE],  # Disco Duro 3,5'
        ["413", SOLID_STATE_DRIVE],  # Disco Duro SSD
        ["88", POWER_SUPPLY],  # Fuentes de poder
        ["8", COMPUTER_CASE],  # Gabinetes
        ["707", COMPUTER_CASE],  # Gabinetes gamer
        ["5", CPU_COOLER],  # Coolers CPU
        ["790", CPU_COOLER],  # Coolers CPU
        ["286", TABLET],  # Tablets
        ["128", EXTERNAL_STORAGE_DRIVE],  # Discos externos 2.5
        ["528", USB_FLASH_DRIVE],  # USB Flash
        ["82", MEMORY_CARD],  # Memory card
        ["20", MOUSE],  # Mouse
        ["703", MOUSE],  # Mouse Gamer
        ["769", PRINTER],  # Impresoras
        ["770", PRINTER],  # Plotter
        ["12", KEYBOARD],  # Teclados
        ["70", HEADPHONES],  # Audífono/Micrófono
        ["13", STEREO_SYSTEM],  # Parlantes
        ["31", UPS],  # UPS
        ["591", GAMING_CHAIR],  # Sillas
        ["864", CELL],
        ["762", TELEVISION],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        offset = 0

        while True:
            if offset >= 300:
                raise Exception("Page overflow: " + url_extension)

            url_webpage = "https://bip.cl/categoria/{}/{}".format(url_extension, offset)

            data = session.get(url_webpage).text

            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("div", "product-box")

            if not product_containers:
                if offset == 0:
                    logging.warning("Empty category: " + url_webpage)
                break

            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append(product_url)

            offset += 20
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        ajax_session = session_with_proxy(extra_args)
        ajax_session.headers["Content-Type"] = (
            "application/x-www-form-urlencoded; charset=UTF-8"
        )
        response = session.get(url)

        if response.status_code in [404, 500]:
            return []

        soup = BeautifulSoup(response.text, "html5lib")

        if soup.find("h1", text="An Error Was Encountered"):
            return []

        name = soup.find("div", "details-image-concept").find("h2").text
        sku = soup.find("input", {"id": "id_producto"}).get("value")
        stocks_container = soup.find("div", "product-buttons").findAll("span")
        stock = 0 if "No Disponible" in [x.text for x in stocks_container] else -1
        price_data = ajax_session.post(
            "https://bip.cl/home/viewProductAjax", "idProd=" + sku
        ).json()
        offer_price = Decimal(price_data["internet_price"].replace(".", ""))
        normal_price = Decimal(price_data["price"].replace(".", ""))

        if normal_price < offer_price:
            offer_price = normal_price

        description = html_to_markdown(
            soup.find("div", "cloth-review").find("div", "tab-content").text
        )

        picture_urls = [
            tag["src"]
            for tag in soup.find("div", "details-image-vertical").findAll("img")
        ]
        condition = (
            "https://schema.org/RefurbishedCondition"
            if "reacondicionado" in name.lower()
            else "https://schema.org/NewCondition"
        )

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
            condition=condition,
        )

        return [p]
