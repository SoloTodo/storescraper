from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    ALL_IN_ONE,
    CASE_FAN,
    COMPUTER_CASE,
    CPU_COOLER,
    EXTERNAL_STORAGE_DRIVE,
    GAMING_CHAIR,
    GAMING_DESK,
    HEADPHONES,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    MEMORY_CARD,
    MICROPHONE,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    NOTEBOOK,
    POWER_SUPPLY,
    PRINTER,
    PROCESSOR,
    SOLID_STATE_DRIVE,
    STEREO_SYSTEM,
    STORAGE_DRIVE,
    TABLET,
    TELEVISION,
    UPS,
    USB_FLASH_DRIVE,
    VIDEO_CARD,
    VIDEO_GAME_CONSOLE,
    RAM,
    CELL,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class KDTec(StoreWithUrlExtensions):
    url_extensions = [
        ["notebook-2", NOTEBOOK],
        ["notebook-gamer", NOTEBOOK],
        ["all-in-one", ALL_IN_ONE],
        ["tablet", TABLET],
        ["macbook", NOTEBOOK],
        ["imac", ALL_IN_ONE],
        ["ipad", TABLET],
        ["sillas-gamer", GAMING_CHAIR],
        ["escritorios-gamer", GAMING_DESK],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["teclado-gamer", KEYBOARD],
        ["audifonos-gamer", HEADPHONES],
        ["mouse-gamer", MOUSE],
        ["disco-duro-externo", EXTERNAL_STORAGE_DRIVE],
        ["disco-duro-interno", STORAGE_DRIVE],
        ["disco-ssd", SOLID_STATE_DRIVE],
        ["monitor", MONITOR],
        ["monitor-gamer", MONITOR],
        ["mouse", MOUSE],
        ["teclados", KEYBOARD],
        ["accesorios-apple", KEYBOARD],
        ["combo-teclado-mouse", KEYBOARD_MOUSE_COMBO],
        ["audifonos", HEADPHONES],
        ["parlante-pc", STEREO_SYSTEM],
        ["microfonos", MICROPHONE],
        ["memoria-ram-notebook", RAM],
        ["memoria-ram-pc", RAM],
        ["pendrive", USB_FLASH_DRIVE],
        ["memoria-flash", MEMORY_CARD],
        ["procesadores", PROCESSOR],
        ["placas-madres", MOTHERBOARD],
        ["tarjetas-de-video", VIDEO_CARD],
        ["fuente-de-poder", POWER_SUPPLY],
        ["ups", UPS],
        ["gabinetes", COMPUTER_CASE],
        ["refrigeracion-cpu", CPU_COOLER],
        ["ventiladores-pc", CASE_FAN],
        ["smart-tv", TELEVISION],
        ["impresoras-laser", PRINTER],
        ["impresoras-tinta", PRINTER],
        ["impresora-multifuncional", PRINTER],
        ["matriz-de-punto", PRINTER],
        ["plotter", PRINTER],
        ["procesador-servidor", PROCESSOR],
        ["memoria-ram-servidor", RAM],
        ["discos-servidor", SOLID_STATE_DRIVE],
        ["celulares", CELL],
        ["pantallas-interactivas", MONITOR],
        ["parlantes-audio", STEREO_SYSTEM],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/"
                "537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 "
                "Safari/537.36"
            }
        )
        product_urls = []
        page = 1
        while True:
            if page > 30:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://kdtec.cl/categoria-producto/{}/".format(
                url_extension
            )

            if page > 1:
                url_webpage += "page/{}/".format(page)

            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html.parser")
            product_containers = soup.findAll("li", "product")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a", "woocommerce-Loop" "Product-link")[
                    "href"
                ]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/"
                "537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 "
                "Safari/537.36"
            }
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]

        json_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )
        for entry in json_data["@graph"]:
            if "@type" in entry and entry["@type"] == "Product":
                product_data = entry
                break
        else:
            raise Exception("No JSON product data found")

        name = product_data["name"]
        sku = product_data.get("sku", None)
        description = product_data["description"]
        price_tags = soup.findAll("span", "woocommerce-Price-amount")
        assert len(price_tags) == 2

        offer_price = Decimal(remove_words(price_tags[0].text))
        normal_price = Decimal(remove_words(price_tags[1].text))

        if offer_price > Decimal(100000000) or normal_price > Decimal(100000000):
            return []

        input_qty = soup.find("input", "qty")
        if input_qty:
            if "max" in input_qty.attrs and input_qty["max"]:
                stock = int(input_qty["max"])
            else:
                stock = -1
        else:
            stock = 0

        if soup.find("span", "font-bold"):
            part_number = soup.find("span", "font-bold").text
        else:
            pn_p = soup.find(
                "div", "woocommerce-product-details__short-description"
            ).find("p")
            if pn_p:
                pn_p_1 = pn_p.text.split("Part number: ")
                pn_p_2 = pn_p.text.split("Número de parte: ")
                if len(pn_p_1) > 1:
                    part_number = pn_p_1[1]
                elif len(pn_p_2) > 1:
                    part_number = pn_p_2[1]
                else:
                    part_number = None
            else:
                part_number = None

        picture_urls = []
        picture_container = soup.find("div", "woocommerce-product-gallery__wrapper")
        for i in picture_container.findAll("img"):
            picture_urls.append(i["src"])

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
            part_number=part_number,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
