import logging
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    PRINTER,
    KEYBOARD,
    HEADPHONES,
    GAMING_CHAIR,
    COMPUTER_CASE,
    RAM,
    POWER_SUPPLY,
    PROCESSOR,
    MOTHERBOARD,
    VIDEO_CARD,
    EXTERNAL_STORAGE_DRIVE,
    USB_FLASH_DRIVE,
    MONITOR,
    KEYBOARD_MOUSE_COMBO,
    NOTEBOOK,
    SOLID_STATE_DRIVE,
    ALL_IN_ONE,
    TELEVISION,
    CELL,
    VIDEO_GAME_CONSOLE,
    MOUSE,
    CPU_COOLER,
    STORAGE_DRIVE,
    MEMORY_CARD,
    TABLET,
    UPS,
    STEREO_SYSTEM,
    WEARABLE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class CtMan(StoreWithUrlExtensions):
    url_extensions = [
        ["notebooks", NOTEBOOK],
        ["memorias-ram-para-laptops", RAM],
        ["memorias-ram", RAM],
        ["memoria-ram-server", RAM],
        ["all-in-one", ALL_IN_ONE],
        ["gabinetes", COMPUTER_CASE],
        ["impresoras", PRINTER],
        ["teclados", KEYBOARD],
        ["teclados-fisicos", KEYBOARD],
        ["audifonos", HEADPHONES],
        ["impresoras-a-color", PRINTER],
        ["coolers-para-pc", CPU_COOLER],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["tarjetas-de-video", VIDEO_CARD],
        ["procesadores", PROCESSOR],
        ["placas-madre", MOTHERBOARD],
        ["packs", PROCESSOR],
        ["discos-duros-externos", EXTERNAL_STORAGE_DRIVE],
        ["ssds-externos", EXTERNAL_STORAGE_DRIVE],
        ["ssd", SOLID_STATE_DRIVE],
        ["pen-drives", USB_FLASH_DRIVE],
        ["monitores", MONITOR],
        ["televisores", TELEVISION],
        ["celulares-y-smartphones", CELL],
        ["fuentes-de-alimentacion", POWER_SUPPLY],
        ["sillas-gamer", GAMING_CHAIR],
        ["gabinetes", COMPUTER_CASE],
        ["notebooks", NOTEBOOK],
        ["kits-de-mouse-y-teclado", KEYBOARD_MOUSE_COMBO],
        ["consolas-de-videojuegos", VIDEO_GAME_CONSOLE],
        ["mouse", MOUSE],
        ["coolers-para-pc", CPU_COOLER],
        ["disco-duro", STORAGE_DRIVE],
        ["tarjeta-de-memoria-flash", MEMORY_CARD],
        ["tablets", TABLET],
        ["ups", UPS],
        ["parlantes", STEREO_SYSTEM],
        ["reloj-inteligente", WEARABLE],
        ["macbooks", NOTEBOOK],
        ["ipads", TABLET],
        ["iphone", CELL],
        ["watch", WEARABLE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = "SoloTodoBot"
        product_urls = []
        page = 1
        while True:
            if page > 25:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://www.ctman.cl/types/{}/" "{}".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-item")
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
        session.headers["User-Agent"] = "SoloTodoBot"
        response = session.get(url)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "lxml")
        key_tag = soup.find("div", "title-description").find(
            "input", {"name": "cart_item[variant_id]"}
        )

        if not key_tag:
            return []

        key = key_tag["value"]
        name = soup.find("h1", "product-name").text.strip()
        sku = soup.find("div", "sku").text.split(":")[1].strip()
        description = html_to_markdown(str(soup.find("div", "product-description")))
        price_tag = soup.find("big", "product-price").find("span", "bootic-price")
        price = Decimal(remove_words(price_tag.text))

        add_to_cart_tag = soup.find("input", value="Agregar al carro")

        if add_to_cart_tag:
            stock = -1
        else:
            stock = 0

        picture_urls = []
        for i in soup.findAll("li", "product-asset"):
            parsed_url = urllib.parse.urlparse(i.find("a")["href"])
            picture_url = parsed_url._replace(
                path=urllib.parse.quote(parsed_url.path)
            ).geturl()
            picture_urls.append(picture_url)

        part_number_tag = soup.find("p", "part-number")
        if part_number_tag:
            part_number = soup.find("p", "part-number").contents[1].strip()
        else:
            part_number = None

        special_tags = soup.findAll("div", "special-tags")

        if special_tags:
            condition = "https://schema.org/RefurbishedCondition"
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
            price,
            price,
            "CLP",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number,
            condition=condition,
        )
        return [p]
