from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup

from storescraper.categories import (
    ALL_IN_ONE,
    HEADPHONES,
    KEYBOARD,
    MONITOR,
    MOTHERBOARD,
    MOUSE,
    NOTEBOOK,
    PRINTER,
    RAM,
    SOLID_STATE_DRIVE,
    STORAGE_DRIVE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import remove_words, session_with_proxy


class XCom(StoreWithUrlExtensions):
    url_extensions = [
        ["productos-nuevos/audio", HEADPHONES],
        [
            "productos-nuevos/componentes-partes-y-piezas_de/discos-notebook",
            SOLID_STATE_DRIVE,
        ],
        [
            "productos-nuevos/componentes-partes-y-piezas_de/discos-ssd",
            SOLID_STATE_DRIVE,
        ],
        ["productos-nuevos/componentes-partes-y-piezas_de/" "memoria-notebook", RAM],
        ["productos-nuevos/componentes-partes-y-piezas_de/memoria-pc", RAM],
        ["productos-nuevos/discos-duros", STORAGE_DRIVE],
        ["productos-nuevos/gabinete-pc", MOTHERBOARD],
        ["productos-nuevos/impresoras", PRINTER],
        ["productos-nuevos/memorias", RAM],
        ["productos-nuevos/monitores-y-proyectores/monitores", MONITOR],
        ["productos-nuevos/mouse", MOUSE],
        ["productos-nuevos/teclados", KEYBOARD],
        [
            "equipos-reacondicionados/reac-componentes-partes/" "disco-duro-externo",
            STORAGE_DRIVE,
        ],
        ["equipos-reacondicionados/all-in-one-reac", ALL_IN_ONE],
        ["equipos-reacondicionados/monitores-reac", MONITOR],
        ["equipos-reacondicionados/notebook-reac", NOTEBOOK],
        ["desarme/disco-duro-desarme", STORAGE_DRIVE],
        ["desarme/memoria-ram-desarme", RAM],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = (
                "https://www.xcom.cl/categoria-producto/{}/"
                "page/{}/".format(url_extension, page)
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("li", "product")
            if not product_containers or "404!" in soup.text:
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]

        json_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )

        for entry in json_data["@graph"]:
            if entry["@type"] == "Product":
                product_data = entry
                break
        else:
            raise Exception("No JSON product data found")

        name = product_data["name"]
        sku = str(product_data["sku"])
        description = product_data.get("description", None)
        picture_urls = [product_data["image"]["@id"]]

        if "PRODUCTOS NUEVOS" in product_data["category"]:
            condition = "https://schema.org/NewCondition"
        else:
            condition = "https://schema.org/RefurbishedCondition"

        input_qty = soup.find("input", "qty")
        if input_qty:
            if "max" in input_qty.attrs and input_qty["max"]:
                stock = int(input_qty["max"])
            else:
                stock = -1
        else:
            stock = 0

        price_wrapper = soup.find("div", "product-summary")
        price_ins = price_wrapper.find("ins")
        if not price_ins:
            return []
        price = Decimal(remove_words(price_ins.text))

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
            condition=condition,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
