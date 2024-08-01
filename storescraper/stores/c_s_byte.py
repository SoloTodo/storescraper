from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    ALL_IN_ONE,
    COMPUTER_CASE,
    CPU_COOLER,
    GAMING_CHAIR,
    HEADPHONES,
    KEYBOARD,
    MICROPHONE,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    NOTEBOOK,
    POWER_SUPPLY,
    PRINTER,
    PROCESSOR,
    RAM,
    SOLID_STATE_DRIVE,
    STEREO_SYSTEM,
    STORAGE_DRIVE,
    TABLET,
    UPS,
    USB_FLASH_DRIVE,
    VIDEO_CARD,
    WEARABLE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class CSByte(StoreWithUrlExtensions):
    preferred_products_for_url_concurrency = 3

    url_extensions = [
        ["audifonos", HEADPHONES],
        ["microfonos", MICROPHONE],
        ["parlantes", STEREO_SYSTEM],
        ["parlantes-gamer", STEREO_SYSTEM],
        ["almacenamiento", SOLID_STATE_DRIVE],
        ["almacenamiento-componentes-gamer", SOLID_STATE_DRIVE],
        ["ssd-almacenamiento-componentes-gamer", SOLID_STATE_DRIVE],
        ["hdd", STORAGE_DRIVE],
        ["almacenamiento-seguridad", STORAGE_DRIVE],
        ["pendrive", USB_FLASH_DRIVE],
        ["fuente-de-poder", POWER_SUPPLY],
        ["gabinete", COMPUTER_CASE],
        ["gabinete-gamer", COMPUTER_CASE],
        ["memoria-ram", RAM],
        ["memoria-ram-componentes-gamer", RAM],
        ["placa-madre", MOTHERBOARD],
        ["placas-madre", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["procesadores-componentes-gamer", PROCESSOR],
        ["refrigeracion", CPU_COOLER],
        ["refrigeracion-gamer", CPU_COOLER],
        ["tarjetas-de-video", VIDEO_CARD],
        ["tarjetas-de-video-componentes-gamer", VIDEO_CARD],
        ["all-in-one", ALL_IN_ONE],
        ["notebook", NOTEBOOK],
        ["impresoras", PRINTER],
        ["monitores", MONITOR],
        ["monitores-gamer", MONITOR],
        ["mouse", MOUSE],
        ["teclado", KEYBOARD],
        ["teclados_zona_gamer", KEYBOARD],
        ["sillas", GAMING_CHAIR],
        ["silla-gamer", GAMING_CHAIR],
        ["tablets", TABLET],
        ["ups", UPS],
        ["audifonos-zona-gamer", HEADPHONES],
        ["mouse-zona-gamer", MOUSE],
        ["wearables", WEARABLE],
        ["fuentes-de-poder", POWER_SUPPLY],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        product_urls = []
        page = 1
        while True:
            if page > 30:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://www.csbyte.cl/product-category/{}/" "".format(
                url_extension
            )

            if page > 1:
                url_webpage += "page/{}/".format(page)

            print(url_webpage)
            response = session.get(url_webpage)

            soup = BeautifulSoup(response.text, "lxml")
            product_wrapper = soup.find("div", "site-content")

            if not product_wrapper:
                raise Exception(response.text)

            product_containers = product_wrapper.findAll("div", "products")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers[-1].findAll("div", "product-grid-item"):
                product_url = container.find("a")["href"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        response = session.get(url)

        if response.url != url:
            print(response.url)
            print(url)
            return []

        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", "product_title").text.strip()

        attributes_table = soup.find("table", "woocommerce-product-attributes")
        condition = "https://schema.org/RefurbishedCondition"

        conditions_table = {
            "Nuevo": "https://schema.org/NewCondition",
            "Refurbished": "https://schema.org/RefurbishedCondition",
            "OpenBox": "https://schema.org/OpenBoxCondition",
            "Seminuevo": "https://schema.org/UsedCondition",
        }

        if attributes_table:
            for row in attributes_table.findAll("tr"):
                label = row.find("th").text.strip()
                if label != "Condición":
                    continue
                value = row.find("td").text.strip()
                condition = conditions_table.get(
                    value, "https://schema.org/RefurbishedCondition"
                )
                break

        if soup.find("form", "variations_form"):
            products = []
            variations = json.loads(
                soup.find("form", "variations_form")["data-product_variations"]
            )
            for product in variations:
                variation_name = name + " - " + " ".join(product["attributes"].values())
                key = str(product["variation_id"])
                sku = product.get("sku", None)
                if product["max_qty"] == "":
                    stock = 0
                else:
                    stock = product["max_qty"]
                price = Decimal(product["display_price"])
                picture_urls = [product["image"]["url"]]
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
                    picture_urls=picture_urls,
                    condition=condition,
                )
                products.append(p)
            return products
        else:
            key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[-1]
            json_data = json.loads(
                soup.findAll("script", {"type": "application/ld+json"})[-1].text
            )["@graph"][1]
            sku = str(json_data["sku"])
            part_number = json_data.get("gtin", None)
            offer = json_data["offers"][0]
            if offer["availability"] == "http://schema.org/InStock":
                stock_p = soup.find("p", "stock")
                if stock_p and "hay existencias" not in stock_p.text.lower():
                    stock = int(stock_p.text.split()[0])
                else:
                    stock = -1
            else:
                stock = 0
            price = Decimal(offer["price"])

            if "image" in json_data:
                picture_urls = [json_data["image"]]
            else:
                picture_urls = None

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
                condition=condition,
                part_number=part_number,
            )
            return [p]
