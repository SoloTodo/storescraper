import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown
from storescraper.categories import (
    PROCESSOR,
    RAM,
    VIDEO_CARD,
    SOLID_STATE_DRIVE,
    POWER_SUPPLY,
    COMPUTER_CASE,
    HEADPHONES,
    MONITOR,
    MOUSE,
    KEYBOARD,
    STORAGE_DRIVE,
    CPU_COOLER,
    MOTHERBOARD,
    GAMING_CHAIR,
    VIDEO_GAME_CONSOLE,
    MEMORY_CARD,
    USB_FLASH_DRIVE,
    STEREO_SYSTEM,
    GAMING_DESK,
    MICROPHONE,
    CASE_FAN,
    EXTERNAL_STORAGE_DRIVE,
)


class PcCom(StoreWithUrlExtensions):
    url_extensions = [
        ["consolas", VIDEO_GAME_CONSOLE],
        ["procesadores", PROCESSOR],
        ["placas-madres", MOTHERBOARD],
        ["memorias-ram", RAM],
        ["tarjetas-de-video", VIDEO_CARD],
        ["ssd-25-sata", SOLID_STATE_DRIVE],
        ["m-2-pcie-nvme", SOLID_STATE_DRIVE],
        ["disco-duro-pc", STORAGE_DRIVE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["gabinetes", COMPUTER_CASE],
        ["refrigeracion-liquida", CPU_COOLER],
        ["cooler-pc", CPU_COOLER],
        ["ventiladores-pc", CASE_FAN],
        ["memoriasd", MEMORY_CARD],
        ["microsd", MEMORY_CARD],
        ["pendrive", USB_FLASH_DRIVE],
        ["audifonos-gamer", HEADPHONES],
        ["audifonos-bluetooth", HEADPHONES],
        ["audifonos-in-ear", HEADPHONES],
        ["parlantes-portatiles", STEREO_SYSTEM],
        ["parlantes-pc", STEREO_SYSTEM],
        ["monitores", MONITOR],
        ["mouse-alambricos", MOUSE],
        ["mouse-inalambricos", MOUSE],
        ["teclado-alambricos", KEYBOARD],
        ["teclado-inalambricos", KEYBOARD],
        ["teclado-smart-tv", KEYBOARD],
        ["mouse-gamers", MOUSE],
        ["teclados-membrana", KEYBOARD],
        ["teclados-mecanicos", KEYBOARD],
        ["sillas-gamers", GAMING_CHAIR],
        ["escritorios-gamers", GAMING_DESK],
        ["microfonos", MICROPHONE],
        ["discos-duros-externos", EXTERNAL_STORAGE_DRIVE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )

        page = 1

        while True:
            if page > 10:
                raise Exception("Page overflow")

            url = "https://pccom.cl/categoria-producto/{}/page/{}/".format(
                url_extension, page
            )
            response = session.get(url)

            if page == 1 and response.status_code == 404:
                raise Exception("Invalid category: " + url)

            soup = BeautifulSoup(response.text, "lxml")
            products = soup.findAll("li", "product")

            if not products:
                if page == 1:
                    logging.warning("Empty path: {}".format(url))
                break

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

        product_data_candidates = soup.findAll(
            "script", {"type": "application/ld+json"}
        )

        for candidate in product_data_candidates:
            candidate_json = json.loads(candidate.text)
            if candidate_json.get("@type", None) == "Product":
                product_data = candidate_json
                break
        else:
            raise Exception("No product data found")

        print(json.dumps(product_data))

        name = product_data["name"]
        sku = str(product_data["sku"])
        key = soup.find("link", {"rel": "shortlink"})["href"].split("=")[1]

        stock_container = soup.find("p", "stock")

        if not stock_container:
            input_qty = soup.find("input", "qty")
            if not input_qty:
                return []
            else:
                stock = -1
        else:
            if "disponible" in stock_container.text:
                stock = int(stock_container.text.split(" disp")[0])
            else:
                stock = 0

        offers_node = product_data["offers"]
        if isinstance(offers_node, list):
            offers_node = offers_node[0]

        offer_price = Decimal(remove_words(offers_node["price"]))
        normal_price = (offer_price * Decimal("1.06")).quantize(0)
        picture_containers = soup.findAll("div", "woocommerce-product-gallery__image")

        picture_urls = [
            ic.find("img")["src"] for ic in picture_containers if ic["data-thumb"]
        ]

        description = html_to_markdown(str(soup.find("div", "woocommerce-tabs")))

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
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
