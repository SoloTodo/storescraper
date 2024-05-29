import re
from decimal import Decimal
from storescraper.categories import (
    PRINTER,
    UPS,
    MOUSE,
    KEYBOARD,
    HEADPHONES,
    STEREO_SYSTEM,
    GAMING_CHAIR,
    COMPUTER_CASE,
    CPU_COOLER,
    RAM,
    POWER_SUPPLY,
    PROCESSOR,
    MOTHERBOARD,
    VIDEO_CARD,
    STORAGE_DRIVE,
    MEMORY_CARD,
    EXTERNAL_STORAGE_DRIVE,
    USB_FLASH_DRIVE,
    MONITOR,
    KEYBOARD_MOUSE_COMBO,
    NOTEBOOK,
    WEARABLE,
    SOLID_STATE_DRIVE,
    CASE_FAN,
    ALL_IN_ONE,
    TABLET,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class Dust2(StoreWithUrlExtensions):
    url_extensions = [
        ["teclados-gamer", KEYBOARD],
        ["mouse-gamer", MOUSE],
        ["audifonos-gamer", HEADPHONES],
        ["sillas-gamer", GAMING_CHAIR],
        ["kits-gamer", KEYBOARD_MOUSE_COMBO],
        ["parlantes-gamer", STEREO_SYSTEM],
        ["monitores-gamer", MONITOR],
        ["monitores", MONITOR],
        ["procesadores", PROCESSOR],
        ["tarjetas-de-video", VIDEO_CARD],
        ["placas-madres", MOTHERBOARD],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["memorias-ram", RAM],
        ["refrigeracion-liquida", CPU_COOLER],
        ["fans-y-controladores", CASE_FAN],
        ["cooler-para-cpu", CPU_COOLER],
        ["discos-m-2", SOLID_STATE_DRIVE],
        ["ssd-y-discos-duros", STORAGE_DRIVE],
        ["discos-y-ssd-externos", EXTERNAL_STORAGE_DRIVE],
        ["audifonos-xbox", HEADPHONES],
        ["impresoras", PRINTER],
        ["respaldo-energia", UPS],
        ["smartband", WEARABLE],
        ["pendrives", USB_FLASH_DRIVE],
        ["accesorios-tablets", TABLET],
        ["notebooks", NOTEBOOK],
        ["equipos", NOTEBOOK],
        ["memorias-ram-notebooks", RAM],
        ["teclados-perifericos", KEYBOARD],
        ["mouse-perifericos", MOUSE],
        ["audifonos-audio", HEADPHONES],
        ["parlantes-audio", STEREO_SYSTEM],
        ["combo-teclado-y-mouse", KEYBOARD_MOUSE_COMBO],
        ["aio", ALL_IN_ONE],
        ["tarjetas-de-memoria", MEMORY_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = "PostmanRuntime/7.29.3"
        endpoint = (
            "https://dust2.gg/page-data/categoria-producto/{}/page-data.json".format(
                url_extension
            )
        )
        print(endpoint)
        response = session.get(endpoint)
        json_response = response.json()

        product_urls = []
        for node in (
            json_response["result"]["pageContext"]["category"]["products"] or []
        ):
            product_urls.append("https://dust2.gg/producto/{}/".format(node["slug"]))
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = "PostmanRuntime/7.29.3"
        slug = re.search(r"/producto/(.+)/", url).groups()[0]
        endpoint = "https://dust2.gg/page-data/producto/{}/page-data.json".format(slug)
        response = session.get(endpoint)
        if response.status_code == 404:
            return []
        json_data = response.json()["result"]["pageContext"]["product"]
        name = json_data["name"]
        key = str(json_data["id"])
        if "PREVENTA" in name:
            stock = 0
        else:
            stock = json_data["stock_quantity"] or 0
        normal_price = Decimal(json_data["price"]).quantize(0)
        offer_price = (normal_price * Decimal("0.93")).quantize(0)
        sku = json_data["sku"]
        picture_urls = [x["src"] for x in json_data["images"]]

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
        )
        return [p]
