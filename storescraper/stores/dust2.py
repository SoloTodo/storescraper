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
        ["24-a-27-pulgadas", MONITOR],
        ["29-superior", MONITOR],
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
        ["audifonos-ps5", HEADPHONES],
        ["audifonos-xbox", HEADPHONES],
        ["impresoras", PRINTER],
        ["respaldo-energia", UPS],
        ["smartband", WEARABLE],
        ["tarjetas-de-memoria-electronica", MEMORY_CARD],
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
        ["monitores-oficina", MONITOR],
        ["24-a-27-pulgadas-oficina", MONITOR],
        ["27-a-32-pulgadas-oficina", MONITOR],
        ["29-o-superior-oficina", MONITOR],
        ["aio", ALL_IN_ONE],
        ["tarjetas-de-memoria", MEMORY_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        endpoint = "https://crmdust2.com/api/index/woo/categories/{}".format(
            url_extension
        )
        response = session.get(endpoint)
        json_response = response.json()

        product_urls = []
        for node in json_response["products"] or []:
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
        json_data = response.json()
        product_id = json_data["result"]["pageContext"]["product"]["id"]
        endpoint = (
            "https://backend.dust2.gg/wp-json/wc/v3/products/{}?consumer_secret="
            "cs_fbb639f8a188712d48121b09573aa46320525b42&consumer_key="
            "ck_478e84c7ccbd134153433e39b77eb922fddcb72d"
        ).format(product_id)
        response = session.get(endpoint)
        product_data = response.json()

        name = product_data["name"]
        sku = product_data["sku"]
        if "id" in product_data:
            key = str(product_data["id"])
        else:
            key = str(product_data["wordpress_id"])
        stock = max(product_data["stock_quantity"] or 0, 0)
        normal_price = (Decimal(product_data["price"])).quantize(0)
        offer_price = (normal_price * Decimal("0.93")).quantize(0)
        picture_urls = [tag["src"] for tag in product_data["images"]]

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
