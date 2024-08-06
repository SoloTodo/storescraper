from decimal import Decimal
import json
import logging

import validators
from bs4 import BeautifulSoup
from storescraper.categories import (
    CELL,
    COMPUTER_CASE,
    CPU_COOLER,
    GAMING_CHAIR,
    GAMING_DESK,
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
    STORAGE_DRIVE,
    TELEVISION,
    VIDEO_CARD,
    VIDEO_GAME_CONSOLE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import remove_words, session_with_proxy


class DiamondPc(StoreWithUrlExtensions):
    url_extensions = [
        ["componentes-de-computacion/gabinetes", COMPUTER_CASE],
        ["componentes-de-computacion/procesadores", PROCESSOR],
        ["componentes-de-computacion/tarjetas-graficas", VIDEO_CARD],
        ["componentes-de-computacion/placas-madre", MOTHERBOARD],
        ["componentes-de-computacion/memorias-ram", RAM],
        ["componentes-de-computacion/fuentes-de-poder", POWER_SUPPLY],
        ["componentes-de-computacion/discos-duro", STORAGE_DRIVE],
        ["componentes-de-computacion/discos-ssd", SOLID_STATE_DRIVE],
        ["componentes-de-computacion/refrigeraciones", CPU_COOLER],
        ["accesorios-de-computacion/zona-gamer/mouse-gamer", MOUSE],
        ["accesorios-de-computacion/zona-gamer/teclados-gamer", KEYBOARD],
        ["accesorios-de-computacion/zona-gamer/audifonos-gamer", HEADPHONES],
        ["accesorios-de-computacion/zona-gamer/sillas-gamer", GAMING_CHAIR],
        ["accesorios-de-computacion/zona-gamer/escritorios-gamer", GAMING_DESK],
        ["accesorios-de-computacion/zona-ofimatica/mouse", MOUSE],
        ["accesorios-de-computacion/zona-ofimatica/teclados", KEYBOARD],
        ["accesorios-de-computacion/zona-ofimatica/audifonos", HEADPHONES],
        ["accesorios-de-computacion/zona-ofimatica/microfonos", MICROPHONE],
        ["monitores-y-televisores/monitores", MONITOR],
        ["monitores-y-televisores/televisores", TELEVISION],
        ["computadores-y-notebook/notebooks-y-accesorios/notebooks", NOTEBOOK],
        ["impresoras-y-suministros/impresoras", PRINTER],
        ["celulares-y-accesorios/celulares-smartphone", CELL],
        ["celulares-y-accesorios/audifonos-inalambricos", HEADPHONES],
        ["consolas", VIDEO_GAME_CONSOLE],
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
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://diamondpc.cl/categoria/{}/page/" "{}/".format(
                url_extension, page
            )
            print(url_webpage)
            data = session.get(url_webpage, timeout=20).text
            soup = BeautifulSoup(data, "html5lib")
            product_container = soup.find("div", "wd-shop-product")
            if not product_container:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_container.findAll("div", "product"):
                product_url = container.find("a")["href"]
                product_urls.append(product_url)

            c = "product_cat-" + url_extension.split("/")[-1]
            product_container_2 = soup.findAll("div", c)
            if len(product_container_2) == 0:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_container_2:
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

        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[-1]

        json_data = json.loads(
            soup.findAll("script", {"type": "application/ld+json"})[-1].text
        )

        for entry in json_data["@graph"]:
            if entry["@type"] == "Product":
                product_data = entry
                break
        else:
            print("No JSON product data found")
            return []

        name = product_data["name"]

        if "sku" in product_data:
            sku = str(product_data["sku"])[:45]
        else:
            sku = None

        description = product_data["description"]

        if soup.find("form", "variations_form"):
            products = []
            variations = json.loads(
                soup.find("form", "variations_form")["data-product_variations"]
            )

            for product in variations:
                variation_name = f"{name} - {''.join(product['attributes'].values())}"
                key = str(product["variation_id"])
                sku = product.get("sku", None)
                stock = 0 if product["max_qty"] == "" else product["max_qty"]
                offer_price = Decimal(product["display_price"])
                normal_price = (offer_price * Decimal("1.08")).quantize(0)
                picture_urls = [product["image"]["url"]]
                p = Product(
                    variation_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    key,
                    stock,
                    normal_price,
                    offer_price,
                    "CLP",
                    description=description,
                    sku=sku,
                    picture_urls=picture_urls,
                )
                products.append(p)

            return products

        offer_price = Decimal(product_data["offers"][0]["price"]).quantize(0)
        second_price = soup.find("div", "wds-second price wds-below")
        if second_price:
            normal_price = Decimal(remove_words(second_price.find("bdi").text))
        else:
            normal_price = offer_price

        stock_p = soup.find("p", "in-stock")
        if stock_p:
            stock = int(stock_p.text.strip().split(" ")[0])
        else:
            stock = 0

        picture_urls = [
            tag["href"].split("?")[0]
            for tag in soup.find(
                "figure", "woocommerce-product-gallery__wrapper"
            ).findAll("a")
            if validators.url(tag["href"])
        ]

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
        )
        return [p]
