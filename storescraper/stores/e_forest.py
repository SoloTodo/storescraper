import logging

from bs4 import BeautifulSoup

from storescraper.categories import (
    HEADPHONES,
    KEYBOARD,
    MONITOR,
    SOLID_STATE_DRIVE,
    WEARABLE,
    NOTEBOOK,
    GAMING_CHAIR,
    USB_FLASH_DRIVE,
    COMPUTER_CASE,
    POWER_SUPPLY,
    CASE_FAN,
    ALL_IN_ONE,
    MOUSE,
    KEYBOARD_MOUSE_COMBO,
    STEREO_SYSTEM,
    TABLET,
    TELEVISION,
    MEMORY_CARD,
    CELL,
)
from storescraper.stores.mercado_libre_chile import MercadoLibreChile
from storescraper.utils import session_with_proxy


class EForest(MercadoLibreChile):
    @classmethod
    def categories(cls):
        return [
            KEYBOARD,
            MONITOR,
            WEARABLE,
            HEADPHONES,
            SOLID_STATE_DRIVE,
            NOTEBOOK,
            GAMING_CHAIR,
            USB_FLASH_DRIVE,
            CASE_FAN,
            MOUSE,
            KEYBOARD_MOUSE_COMBO,
            TABLET,
            TELEVISION,
            MEMORY_CARD,
            CELL,
            COMPUTER_CASE,
            POWER_SUPPLY,
            STEREO_SYSTEM,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["computacion/accesorios-pc-gaming/audifonos", HEADPHONES],
            ["computacion/accesorios-pc-gaming/sillas-gamer", GAMING_CHAIR],
            ["computacion/almacenamiento/discos-accesorios", SOLID_STATE_DRIVE],
            ["computacion/almacenamiento/pen-drives", USB_FLASH_DRIVE],
            ["computacion/componentes-pc/discos-accesorios", SOLID_STATE_DRIVE],
            ["computacion/componentes-pc/gabinetes-soportes-pc", COMPUTER_CASE],
            ["computacion/componentes-pc/fuentes-alimentacion", POWER_SUPPLY],
            ["computacion/componentes-pc/coolers-ventiladores", CASE_FAN],
            ["computacion/componentes-pc/otros", COMPUTER_CASE],
            ["computacion/monitores-accesorios", MONITOR],
            ["computacion/notebooks-accesorios/notebooks", NOTEBOOK],
            ["computacion/pc-escritorio", ALL_IN_ONE],
            ["computacion/perifericos-accesorios/teclados", KEYBOARD],
            ["computacion/perifericos-accesorios/mouses", MOUSE],
            ["mouses-teclados-controles-kits-mouse-teclado", KEYBOARD_MOUSE_COMBO],
            ["perifericos-pc-parlantes", STEREO_SYSTEM],
            ["computacion/tablets-accesorios/tablets", TABLET],
            ["apple", NOTEBOOK],
            ["relojes-joyas", WEARABLE],
            ["electronica-audio-video/audio/audio-portatil-accesorios", STEREO_SYSTEM],
            ["electronica-audio-video/audio/audifonos", HEADPHONES],
            ["electronica-audio-video/audio/parlantes-subwoofers", STEREO_SYSTEM],
            ["electronica-audio-video/audio/home-theater", STEREO_SYSTEM],
            ["electronica-audio-video/audio/asistentes-virtuales", STEREO_SYSTEM],
            ["electronica-audio-video/televisores", TELEVISION],
            ["consolas-videojuegos", HEADPHONES],
            ["celulares-telefonia/accesorios-celulares/memorias", MEMORY_CARD],
            ["celulares-telefonia/accesorios-celulares/parlantes", STEREO_SYSTEM],
            ["celulares-telefonia/accesorios-celulares/manos-libres", HEADPHONES],
            ["celulares-telefonia/celulares-smartphones", CELL],
            ["celulares-telefonia/smartwatches-accesorios", WEARABLE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception("Page overflow: " + url_extension)
                index = str(50 * (page - 1) + 1)
                url_webpage = (
                    "https://www.eforest.cl/listado/"
                    "{}/_Desde_{}_NoIndex_True".format(url_extension, index)
                )
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "lxml")
                product_containers = soup.findAll("li", "ui-search-layout__item")
                if not product_containers:
                    if page == 1:
                        logging.warning("Empty category: " + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find("a", "ui-search-link")["href"]
                    product_urls.append(product_url.split("#")[0])
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        # Remove the seller because we consider MecadoLibreLg to be a
        # standalone retailer, in particular because the LG WTB system
        # only displays entries without a seller (not from marketplaces)
        # and we want to consider MercadoLibreLG for that.
        products = super().products_for_url(
            url, category=category, extra_args=extra_args
        )

        for product in products:
            if "openbox" in product.name.lower():
                product.condition = "https://schema.org/RefurbishedCondition"
            product.seller = None

        return products
