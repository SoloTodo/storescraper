import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    PROCESSOR,
    MOTHERBOARD,
    RAM,
    SOLID_STATE_DRIVE,
    NOTEBOOK,
    COMPUTER_CASE,
    CPU_COOLER,
    MONITOR,
    VIDEO_CARD,
    STEREO_SYSTEM,
    MOUSE,
    KEYBOARD,
    HEADPHONES,
    EXTERNAL_STORAGE_DRIVE,
    STORAGE_DRIVE,
    USB_FLASH_DRIVE,
    GAMING_CHAIR,
    PRINTER,
    POWER_SUPPLY,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class FiestaLan(StoreWithUrlExtensions):
    url_extensions = [
        ["notebooks", NOTEBOOK],
        ["impresoras", PRINTER],
        ["motherboard", MOTHERBOARD],
        ["ram", RAM],
        ["almacenamiento/disco-duro-externo", EXTERNAL_STORAGE_DRIVE],
        ["almacenamiento/ssd", SOLID_STATE_DRIVE],
        ["almacenamiento/hdd-almacenamiento", STORAGE_DRIVE],
        ["almacenamiento/m2", SOLID_STATE_DRIVE],
        ["almacenamiento/nvme", SOLID_STATE_DRIVE],
        ["almacenamiento/pendrive", USB_FLASH_DRIVE],
        ["procesadores", PROCESSOR],
        ["gabinetes/gabinetes-gabinetes", COMPUTER_CASE],
        ["gabinetes/fuentes-de-poder", POWER_SUPPLY],
        ["refrigeracion", CPU_COOLER],
        ["monitores", MONITOR],
        ["tarjetas-de-video", VIDEO_CARD],
        ["accesorios-computacion/parlantes", STEREO_SYSTEM],
        ["accesorios-computacion/ratones", MOUSE],
        ["accesorios-computacion/audifonos", HEADPHONES],
        [
            "accesorios-computacion/teclados-y-mouse-accesorios-computacion",
            KEYBOARD,
        ],
        ["accesorios-computacion/sillas-gamer", GAMING_CHAIR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = (
                "https://fiestalan.cl/categoria-producto/"
                "{}/page/{}".format(url_extension, page)
            )
            data = session.get(url_webpage, verify=False).text
            soup = BeautifulSoup(data, "html.parser")
            product_containers = soup.findAll("li", "product")
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
        session = session_with_proxy(extra_args)
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        stock_tag = soup.find("p", "stock")

        if not stock_tag:
            return []

        name = soup.find("h1", "product_title").text.replace("\n\t", "")
        sku = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[1]
        stock = -1 if stock_tag.text == "Hay existencias" else 0
        price = Decimal(remove_words(soup.find("p", "price").findAll("bdi")[-1].text))
        picture_containers = soup.find("div", "woocommerce-product-gallery").findAll(
            "img"
        )
        picture_urls = [tag["src"] for tag in picture_containers]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            "CLP",
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
