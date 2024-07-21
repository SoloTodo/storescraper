import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    COMPUTER_CASE,
    MOTHERBOARD,
    PROCESSOR,
    RAM,
    STORAGE_DRIVE,
    SOLID_STATE_DRIVE,
    EXTERNAL_STORAGE_DRIVE,
    HEADPHONES,
    MOUSE,
    MONITOR,
    KEYBOARD,
    CPU_COOLER,
    VIDEO_CARD,
    GAMING_CHAIR,
    NOTEBOOK,
    POWER_SUPPLY,
    CASE_FAN,
    STEREO_SYSTEM,
    VIDEO_GAME_CONSOLE,
    MEMORY_CARD,
    KEYBOARD_MOUSE_COMBO,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class ETChile(StoreWithUrlExtensions):
    url_extensions = [
        # Componentes
        ["discos-duros", STORAGE_DRIVE],
        ["ssd", SOLID_STATE_DRIVE],
        ["gabinetes", COMPUTER_CASE],
        ["memorias", RAM],
        ["placas-madres", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["psu-fuentes-de-poder", POWER_SUPPLY],
        ["ventiladores", CASE_FAN],
        ["water-cooling", CPU_COOLER],
        ["tarjetas-de-video", VIDEO_CARD],
        # Perifericos
        ["audifonos", HEADPHONES],
        ["parlantes-y-equipo-de-sonido", STEREO_SYSTEM],
        ["mouse", MOUSE],
        ["teclados", KEYBOARD],
        # Productos
        ["discos-externos", EXTERNAL_STORAGE_DRIVE],
        ["hdd-interno", STORAGE_DRIVE],
        ["memorias-flash", MEMORY_CARD],
        ["ssd-externo", EXTERNAL_STORAGE_DRIVE],
        ["ssd-interno-almacenamiento-y-drives", SOLID_STATE_DRIVE],
        ["monitores", MONITOR],
        ["notebooks", NOTEBOOK],
        ["packs-y-combos", KEYBOARD_MOUSE_COMBO],
        # Empty sections as of 2024-06-21
        ["sillas", GAMING_CHAIR],
        ["consolas-y-vr", VIDEO_GAME_CONSOLE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )

        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://etchile.net/categorias/{}/".format(url_extension)
            if page > 1:
                url_webpage += "page/{}/".format(page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-small")

            if not product_containers:
                if page == 1:
                    logging.warning("Emtpy category: " + url_extension)
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
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )

        response = session.get(url)
        if response.status_code == 404:
            return []
        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", "product-title").text.strip()
        if soup.find("form", "variations_form"):
            product_variations = json.loads(
                soup.find("form", "variations_form")["data-product_variations"]
            )
            products = []
            for variation in product_variations:
                variation_name = (
                    name + " - " + variation["attributes"]["attribute_color"]
                )
                sku = variation["sku"]
                key = str(variation["variation_id"])
                stock = variation["max_qty"]
                price = Decimal(variation["display_price"]).quantize(0)
                picture_urls = [variation["image"]["url"]]

                p = Product(
                    variation_name,
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
                    part_number=sku,
                    picture_urls=picture_urls,
                )
                products.append(p)
            return products

        else:
            sku = None
            if soup.find("span", "sku"):
                sku = soup.find("span", "sku").text
            key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[-1]

            stock_tag = soup.find("input", {"name": "quantity"})
            if stock_tag:
                if "max" in stock_tag.attrs:
                    if "" == stock_tag["max"]:
                        stock = -1
                    else:
                        stock = int(stock_tag["max"])
                else:
                    stock = 1
            else:
                stock = 0

            if soup.find("p", "price").find("ins"):
                price = Decimal(
                    remove_words(soup.find("p", "price").find("ins").text.strip())
                )
            else:
                price = Decimal(remove_words(soup.find("p", "price").text.strip()))

            picture_urls = [
                tag.find("img")["data-src"].split("?")[0]
                for tag in soup.findAll("li", "product_thumbnail_item")
            ]
            description = html_to_markdown(
                str(soup.find("div", "woocommerce-Tabs-panel--description"))
            )
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
                part_number=sku,
                picture_urls=picture_urls,
                description=description,
            )
            return [p]
