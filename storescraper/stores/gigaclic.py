import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    MOTHERBOARD,
    PROCESSOR,
    VIDEO_CARD,
    RAM,
    COMPUTER_CASE,
    POWER_SUPPLY,
    CPU_COOLER,
    KEYBOARD,
    HEADPHONES,
    PRINTER,
    MONITOR,
    SOLID_STATE_DRIVE,
    STORAGE_DRIVE,
    EXTERNAL_STORAGE_DRIVE,
    STEREO_SYSTEM,
    USB_FLASH_DRIVE,
    MEMORY_CARD,
    WEARABLE,
    UPS,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Gigaclic(StoreWithUrlExtensions):
    url_extensions = [
        ["accesorios/placas-madres", MOTHERBOARD],
        ["accesorios/procesadores", PROCESSOR],
        ["accesorios/tarjetas-de-video", VIDEO_CARD],
        ["accesorios/memorias-ram", RAM],
        ["accesorios/gabinetes", COMPUTER_CASE],
        ["accesorios/fuentes-de-poder", POWER_SUPPLY],
        ["accesorios/refrigeracion", CPU_COOLER],
        ["accesorios/mouse-y-teclados", KEYBOARD],
        ["accesorios/audifonos-gamer", HEADPHONES],
        ["accesorios/accesorios-gamer", HEADPHONES],
        ["impresoras", PRINTER],
        ["monitores", MONITOR],
        ["almacenamiento/discos-estado-solido", SOLID_STATE_DRIVE],
        ["almacenamiento/discos-duro-notebook", EXTERNAL_STORAGE_DRIVE],
        ["almacenamiento/discos-duro-pcs", STORAGE_DRIVE],
        ["almacenamiento/discos-portatiles", EXTERNAL_STORAGE_DRIVE],
        ["almacenamiento/discos-sobremesa", EXTERNAL_STORAGE_DRIVE],
        ["almacenamiento/memorias-sd-o-microsd", MEMORY_CARD],
        ["almacenamiento/pendrive", USB_FLASH_DRIVE],
        ["almacenamiento/accesorios-almacenamiento", STORAGE_DRIVE],
        ["electronica/audifonos", HEADPHONES],
        ["electronica/parlantes", STEREO_SYSTEM],
        ["electronica/pulseras-inteligentes", WEARABLE],
        ["mas-categorias/mouse-y-teclados-mas-categorias", KEYBOARD],
        ["mas-categorias/accesorios-ups", UPS],
        ["mas-categorias/accesorios-ps4-ps5-xbox/", EXTERNAL_STORAGE_DRIVE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        done = False
        while not done:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = (
                "https://gigaclic.cl/product-category/{}/"
                "?product-page={}".format(url_extension, page)
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("li", "product")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a")["href"]
                if product_url in product_urls:
                    done = True
                    break
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h2", "product_title").text.strip()
        sku = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[1]

        if soup.find("span", "inventory_status out-stock"):
            stock = 0
        elif soup.find("p", "stock in-stock"):
            stock = int(soup.find("p", "stock in-stock").text.split()[0])
        else:
            stock = -1

        price_container = soup.find("p", "price")
        if not price_container.text:
            return []

        if price_container.find("ins"):
            price = Decimal(remove_words(price_container.find("ins").text))
        else:
            price = Decimal(remove_words(price_container.text))
        picture_urls = [
            tag["src"]
            for tag in soup.find("div", "woocommerce-product-gallery").findAll("img")
        ]
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
