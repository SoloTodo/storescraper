import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    ALL_IN_ONE,
    TABLET,
    NOTEBOOK,
    MOTHERBOARD,
    PROCESSOR,
    CPU_COOLER,
    VIDEO_CARD,
    RAM,
    COMPUTER_CASE,
    POWER_SUPPLY,
    STORAGE_DRIVE,
    SOLID_STATE_DRIVE,
    MONITOR,
    HEADPHONES,
    USB_FLASH_DRIVE,
    PRINTER,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class WebRedes(StoreWithUrlExtensions):
    url_extensions = [
        ["60-notebooks", NOTEBOOK],
        ["62-discos-hdd", STORAGE_DRIVE],
        ["63-discos-ssd", SOLID_STATE_DRIVE],
        ["91-memorias-ram", RAM],
        ["228-placas-madre", MOTHERBOARD],
        ["229-procesadores", PROCESSOR],
        ["230-tarjetas-de-video", VIDEO_CARD],
        ["231-gabinetes", COMPUTER_CASE],
        ["232-fuentes-de-poder", POWER_SUPPLY],
        ["239-monitores", MONITOR],
        ["240-accesorios-", USB_FLASH_DRIVE],
        ["249-nvme", SOLID_STATE_DRIVE],
        ["258-impresoras", PRINTER],
        ["260-multifuncional", PRINTER],
        ["269-refrigeracion-y-ventiladores", CPU_COOLER],
        ["272-audifonos", HEADPHONES],
        ["291-tablets", TABLET],
        ["298-memoria-ram", RAM],
        ["299-procesador", PROCESSOR],
        ["300-fuentes-de-poder", POWER_SUPPLY],
        ["302-almacenamiento", STORAGE_DRIVE],
        ["318-todo-en-uno", ALL_IN_ONE],
        ["320-notebooks-gamer", NOTEBOOK],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://store.webredes.cl/{}?page={}".format(
                url_extension, page
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html5lib")
            product_containers = soup.find("div", "products")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers.findAll("article"):
                product_url = container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        json_info = json.loads(
            soup.find("div", {"id": "product-details"})["data-product"]
        )
        print(json.dumps(json_info))
        name = json_info["reference"] + " - " + json_info["name"]
        key = str(json_info["id_product"])
        sku = str(json_info["reference"]) or None
        stock = json_info["quantity"]
        normal_price = Decimal(json_info["price_amount"])
        offer_price = (normal_price * Decimal(0.95)).quantize(0)

        picture_urls = [
            image["bySize"]["large_default"]["url"] for image in json_info["images"]
        ]
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
        )
        return [p]
