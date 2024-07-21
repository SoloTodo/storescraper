from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    CELL,
    COMPUTER_CASE,
    CPU_COOLER,
    GAMING_CHAIR,
    HEADPHONES,
    KEYBOARD,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    NOTEBOOK,
    POWER_SUPPLY,
    PROCESSOR,
    RAM,
    SOLID_STATE_DRIVE,
    STORAGE_DRIVE,
    TABLET,
    VIDEO_CARD,
    EXTERNAL_STORAGE_DRIVE,
    USB_FLASH_DRIVE,
    WEARABLE,
    ALL_IN_ONE,
    KEYBOARD_MOUSE_COMBO,
    STEREO_SYSTEM,
    TELEVISION,
    PRINTER,
    VIDEO_GAME_CONSOLE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown, remove_words


class PulseTech(StoreWithUrlExtensions):
    url_extensions = [
        ["discos-ssd-internos", SOLID_STATE_DRIVE],
        ["discos-hdd-internos", STORAGE_DRIVE],
        ["almacenamiento-externo", EXTERNAL_STORAGE_DRIVE],
        ["memorias-flash", USB_FLASH_DRIVE],
        ["celulares", CELL],
        ["tablet", TABLET],
        ["relojes", WEARABLE],
        ["all-in-one", ALL_IN_ONE],
        ["notebooks-de-14", NOTEBOOK],
        ["notebooks-de-15-6", NOTEBOOK],
        ["notebooks-de-16", NOTEBOOK],
        ["notebooks-gamer", NOTEBOOK],
        ["memorias-notebook", RAM],
        ["cpu-amd-am4", PROCESSOR],
        ["cpu-am5", PROCESSOR],
        ["cpu-intel-s1200", PROCESSOR],
        ["cpu-intel-1700", PROCESSOR],
        ["placa-madre-am4", MOTHERBOARD],
        ["placas-madre-am5", MOTHERBOARD],
        ["placas-madres-intel-s1200", MOTHERBOARD],
        ["placas-madres-intel-1700", MOTHERBOARD],
        ["memorias-notebook", RAM],
        ["memorias-pc", RAM],
        ["tarjetas-de-video", VIDEO_CARD],
        ["gabinetes", COMPUTER_CASE],
        ["refrigeracion", CPU_COOLER],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["teclados", KEYBOARD],
        ["mouse", MOUSE],
        ["combo-teclado-mouse", KEYBOARD_MOUSE_COMBO],
        ["audifonos-in-ear", HEADPHONES],
        ["audifonos-on-ear", HEADPHONES],
        ["parlantes", STEREO_SYSTEM],
        ["monitores", MONITOR],
        ["televisores", TELEVISION],
        ["impresion-laser", PRINTER],
        ["impresion-tinta", PRINTER],
        ["otras-impresoras", PRINTER],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["audifonos-gamer", HEADPHONES],
        ["teclados-gamer", KEYBOARD],
        ["mouse-gamer", MOUSE],
        ["sillas-y-mesas-gamer", GAMING_CHAIR],
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
                "https://www.pulsetech.cl/collections/{}?view=view-48&page={}".format(
                    url_extension, page
                )
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("li", "productgrid--item")

            if not product_containers:
                if page == 1:
                    logging.warning("empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = "https://www.pulsetech.cl" + container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        product_json_tag = soup.find("script", {"data-section-type": "static-product"})
        product_json = json.loads(product_json_tag.text)["product"]
        picture_urls = ["https:" + x for x in product_json["images"]]
        description = html_to_markdown(product_json["description"])
        price_tags = soup.findAll("span", "price")
        offer_price = Decimal(remove_words(price_tags[0].text))
        normal_price = Decimal(remove_words(price_tags[1].text))
        assert len(product_json["variants"]) == 1
        product_entry = product_json["variants"][0]
        name = product_entry["name"]
        key = str(product_entry["id"])
        sku = product_entry["sku"] or None
        if product_entry["available"]:
            stock = -1
        else:
            stock = 0

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
            picture_urls=picture_urls,
            description=description,
            part_number=sku,
        )
        return [p]
