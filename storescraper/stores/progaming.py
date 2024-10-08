from decimal import Decimal
import logging
from bs4 import BeautifulSoup

from storescraper.categories import (
    SOLID_STATE_DRIVE,
    NOTEBOOK,
    POWER_SUPPLY,
    COMPUTER_CASE,
    RAM,
    MOTHERBOARD,
    PROCESSOR,
    CPU_COOLER,
    VIDEO_CARD,
    HEADPHONES,
    KEYBOARD_MOUSE_COMBO,
    MOUSE,
    STEREO_SYSTEM,
    KEYBOARD,
    MONITOR,
    GAMING_CHAIR,
    USB_FLASH_DRIVE,
    WEARABLE,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, session_with_proxy


class Progaming(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            NOTEBOOK,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_CARD,
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
            MOUSE,
            STEREO_SYSTEM,
            KEYBOARD,
            MONITOR,
            GAMING_CHAIR,
            USB_FLASH_DRIVE,
            WEARABLE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["componentes/almacenamiento-componentes", SOLID_STATE_DRIVE],
            ["componentes/computadores-y-notebooks", NOTEBOOK],
            ["componentes/fuentes-poder", POWER_SUPPLY],
            ["componentes/gabinetes-componentes", COMPUTER_CASE],
            ["componentes/memorias-ram-componentes", RAM],
            ["componentes/placas-madres", MOTHERBOARD],
            ["componentes/procesadores-componentes", PROCESSOR],
            ["componentes/refrigeracion", CPU_COOLER],
            ["componentes/tarjetas-video", VIDEO_CARD],
            ["perifericos/audifonos-perifericos", HEADPHONES],
            ["perifericos/kits-perifericos", KEYBOARD_MOUSE_COMBO],
            ["perifericos/mouse-perifericos", MOUSE],
            ["perifericos/parlantes-perifericos", STEREO_SYSTEM],
            ["perifericos/teclados", KEYBOARD],
            ["monitores-2/monitor-gamer", MONITOR],
            ["sillas-gamers/sillas-sillones", GAMING_CHAIR],
            ["otros-productos/pendrivers-memorias", USB_FLASH_DRIVE],
            ["otros-productos/relojes-inteligentes", WEARABLE],
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
                url_webpage = (
                    "https://www.progaming.cl/categoria-producto/"
                    "{}/page/{}/".format(url_extension, page)
                )
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "lxml")
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
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("=")[-1]

        name = soup.find("h3", "product_title").text.strip()
        sku = soup.find("span", "sku").text.strip()
        offer_price_tag = soup.find("p", "price").text.lower()

        if "el precio actual es:" in offer_price_tag:
            offer_price = Decimal(
                remove_words(offer_price_tag.split("el precio actual es:")[1])
            )
        else:
            offer_price = Decimal(remove_words(soup.find("p", "price").text))

        normal_price = Decimal(remove_words(soup.find("h5", {"id": "precio3"}).text))

        stock_tag = soup.find("input", "qty")

        if stock_tag:
            stock = int(stock_tag["value"])
        else:
            stock = 0

        picture_container = soup.find("div", "woocommerce-product-gallery__wrapper")
        picture_urls = []
        for a in picture_container.findAll("a"):
            picture_urls.append(a["href"])

        description_tag = soup.find("div", {"id": "tab-description"})
        if description_tag:
            description = html_to_markdown(description_tag.text)
        else:
            description = None

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
            description=description,
        )
        return [p]
