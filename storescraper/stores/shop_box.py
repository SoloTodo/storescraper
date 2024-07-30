import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import (
    ALL_IN_ONE,
    CPU_COOLER,
    GAMING_DESK,
    HEADPHONES,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    MEMORY_CARD,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    NOTEBOOK,
    POWER_SUPPLY,
    PRINTER,
    PROCESSOR,
    RAM,
    STEREO_SYSTEM,
    STORAGE_DRIVE,
    TABLET,
    TELEVISION,
    USB_FLASH_DRIVE,
    WEARABLE,
)


class ShopBox(StoreWithUrlExtensions):
    url_extensions = [
        ["accesorios-surface/surface-arc", MOUSE],
        ["audio-tv-y-video/parlantes", STEREO_SYSTEM],
        ["audio-tv-y-video/parlantes-bluetooth", STEREO_SYSTEM],
        ["audio-tv-y-video/televisores", TELEVISION],
        [
            "celulares-y-smarthphones/accesorios-celulares-y-smarthphones/audifonos",
            HEADPHONES,
        ],
        [
            "computacion/accesorios-computacion/audifonos-accesorios-computacion",
            HEADPHONES,
        ],
        ["computacion/accesorios-computacion/coolers", CPU_COOLER],
        [
            "computacion/accesorios-computacion/kit-mouse-y-teclado",
            KEYBOARD_MOUSE_COMBO,
        ],
        ["computacion/accesorios-computacion/mouse", MOUSE],
        [
            "computacion/accesorios-computacion/teclados-accesorios-computacion",
            KEYBOARD,
        ],
        ["computacion/almacenamiento/discos-duros", STORAGE_DRIVE],
        ["computacion/almacenamiento/pendrive", USB_FLASH_DRIVE],
        ["computacion/almacenamiento/tarjetas-de-memoria", MEMORY_CARD],
        ["computacion/componentes-para-pc/fuentes-de-poder", POWER_SUPPLY],
        ["computacion/componentes-para-pc/memorias-ram", RAM],
        ["computacion/componentes-para-pc/placas-madre", MOTHERBOARD],
        ["computacion/componentes-para-pc/procesadores", PROCESSOR],
        ["computacion/escritorio/all-in-one", ALL_IN_ONE],
        ["computacion/escritorio/imac-escritorio", ALL_IN_ONE],
        ["computacion/escritorio/monitores-escritorio", MONITOR],
        ["computacion/notebooks/2-en-1-notebooks", NOTEBOOK],
        ["computacion/notebooks/portatil", NOTEBOOK],
        ["computacion/tablets", TABLET],
        ["hogar/muebles/escritorios", GAMING_DESK],
        ["impresoras-y-scanners/impresoras-de-fotografias", PRINTER],
        ["impresoras-y-scanners/impresoras-ink-jet-impresoras-y-scanners", PRINTER],
        ["impresoras-y-scanners/impresoras-laser-impresoras-y-scanners", PRINTER],
        [
            "impresoras-y-scanners/impresoras-multifuncionales-impresoras-y-scanners",
            PRINTER,
        ],
        ["tecnologia-portatil/relojes", WEARABLE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        page = 1

        while True:
            if page > 20:
                raise Exception("Page overflow: " + url_extension)

            url = f"https://www.shopbox.cl/product-category/{url_extension}/page/{page}"
            print(url)
            response = session.get(url)

            if response.status_code == 404:
                if page == 1:
                    raise Exception(f"Empty category: {url}")
                break

            soup = BeautifulSoup(response.text, "lxml")
            products = soup.findAll("div", "product")
            for product in products:
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, "lxml")
        products_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[1].text
        )
        products = []
        key = soup.find("link", {"rel": "shortlink"})["href"].split("=")[-1]

        for offer in products_data["offers"]:
            original_name = products_data["name"]
            name = original_name[:256]
            sku = str(products_data["sku"])
            prices = [
                int(price.text.replace(".", "").replace("$", ""))
                for price in soup.find("table", {"id": "tabla-precios"}).findAll(
                    "span", "woocommerce-Price-amount amount"
                )
            ]
            prices = sorted(prices)[:2]
            offer_price = Decimal(prices[0])
            normal_price = Decimal(prices[1])

            if normal_price > Decimal("100000000") or offer_price > Decimal(
                "100000000"
            ):
                return []

            stock = -1 if offer["availability"] == "http://schema.org/InStock" else 0
            picture_urls = [
                tag.find("a")["href"]
                for tag in soup.findAll("div", "woocommerce-product-gallery__image")
            ]
            description = html_to_markdown(products_data["description"])

            if "reacondicionado" in original_name.lower():
                condition = "https://schema.org/Refurbished"
            elif "segunda mano" in original_name.lower():
                condition = "https://schema.org/UsedCondition"
            elif "caja abierta" in original_name.lower():
                condition = "https://schema.org/OpenBoxCondition"
            else:
                condition = "https://schema.org/NewCondition"

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
                condition=condition,
            )
            products.append(p)

        return products
