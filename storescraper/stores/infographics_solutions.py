import json
import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import (
    MOTHERBOARD,
    RAM,
    PROCESSOR,
    VIDEO_CARD,
    HEADPHONES,
    MOUSE,
    SOLID_STATE_DRIVE,
    KEYBOARD,
    COMPUTER_CASE,
    STORAGE_DRIVE,
    POWER_SUPPLY,
    CPU_COOLER,
    GAMING_CHAIR,
    USB_FLASH_DRIVE,
    CASE_FAN,
    EXTERNAL_STORAGE_DRIVE,
    NOTEBOOK,
    MONITOR,
    VIDEO_GAME_CONSOLE,
    TELEVISION,
    PRINTER,
)


class InfographicsSolutions(StoreWithUrlExtensions):
    url_extensions = [
        ["gabinetes", COMPUTER_CASE],
        ["refrigeracion-liquida", CPU_COOLER],
        ["refrigeracion-aire", CPU_COOLER],
        ["ventiladores-fans", CASE_FAN],
        ["disco-duro", STORAGE_DRIVE],
        ["ssd-sata-2-5", SOLID_STATE_DRIVE],
        ["ssd-sata-m-2", SOLID_STATE_DRIVE],
        ["ssd-nvme-pcie", SOLID_STATE_DRIVE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["placas-madre", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["memorias-ram", RAM],
        ["tarjetas-graficas", VIDEO_CARD],
        ["audifonos-headset", HEADPHONES],
        ["teclados-gamer", KEYBOARD],
        ["mouse-gamer", MOUSE],
        ["sillas-gamer", GAMING_CHAIR],
        ["audifonos", HEADPHONES],
        ["teclados", KEYBOARD],
        ["mouse", MOUSE],
        ["disco-duro-externo", EXTERNAL_STORAGE_DRIVE],
        ["ssd-externo", EXTERNAL_STORAGE_DRIVE],
        ["pendrive", USB_FLASH_DRIVE],
        ["memorias-ram-notebook-ddr4", RAM],
        ["notebook-gamer", NOTEBOOK],
        ["notebook-ofimatica", NOTEBOOK],
        ["monitores", MONITOR],
        ["todas-las-consolas", VIDEO_GAME_CONSOLE],
        ["televisores", TELEVISION],
        ["impresoras", PRINTER],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        session.headers["Cookie"] = "_lscache_vary=a"
        product_urls = []
        page = 1

        while True:
            url = (
                "https://infographicssolutions.cl/categoria-producto/"
                "{}/page/{}/".format(url_extension, page)
            )
            print(url)

            if page > 15:
                raise Exception("Page overflow: " + str(page))

            res = session.get(url)
            if res.status_code == 404:
                if page == 1:
                    logging.warning("Invalid category: " + url)
                break

            soup = BeautifulSoup(res.text, "html.parser")
            products = soup.findAll("div", "product-grid-item")

            for product in products:
                product_urls.append(product.find("a")["href"])

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
        session.headers["Cookie"] = "_lscache_vary=a"

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, "html.parser")
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[1].strip()

        soup_jsons = soup.findAll("script", {"type": "application/ld+json"})

        if len(soup_jsons) < 2:
            return []

        json_data = json.loads(soup_jsons[1].text)

        if "@graph" not in json_data:
            return []

        for entry in json_data["@graph"]:
            if entry["@type"] == "Product":
                product_data = entry
                break
        else:
            raise Exception("No data entry found")

        if "name" in product_data:
            name = product_data["name"]
            sku = str(product_data["sku"])
            offer_price = Decimal(product_data["offers"][0]["price"])
            normal_price = round((offer_price * Decimal("1.1")).quantize(0), -1)
        else:
            json_data_2 = json.loads(soup_jsons[0].text)["@graph"]
            for entry in json_data_2["@graph"]:
                if entry["@type"] == "WebPage":
                    product_data_2 = entry
                    break
            else:
                raise Exception("No Webpage entry found")
            name = product_data_2["name"]
            wds = soup.find("div", "wd-single-price")
            if wds.find("div", "wds-first").find("ins"):
                offer_price = Decimal(
                    wds.find("div", "wds-first")
                    .find("ins")
                    .text.split("$")[-1]
                    .replace(".", "")
                )
            else:
                offer_price = Decimal(
                    wds.find("div", "wds-first")
                    .find("bdi")
                    .text.split("$")[-1]
                    .replace(".", "")
                )
            normal_price = Decimal(
                wds.find("div", "wds-second")
                .find("span", "amount")
                .text.split("$")[-1]
                .replace(".", "")
            )
            sku = key

        stock_container = soup.find("div", "vc_custom_1644417722193").find("p", "stock")
        short_description = product_data.get("description", "")

        description = html_to_markdown(str(soup.find("div", {"id": "tab-description"})))
        if description == "None\n":
            description = html_to_markdown(
                str(soup.find("div", "woocommerce-product-details__short-description"))
            )

        detalle_envio_tag = soup.find("div", "mensaje-clase-envio")

        if "VENTA" in name.upper() and "PRE" in name.upper():
            # Preventa
            stock = 0
            description = "PREVENTA " + description
        elif "LLEGADA" in short_description.upper():
            # Preventa
            stock = 0
            description = "PREVENTA " + description
        elif detalle_envio_tag and "DÍAS" in detalle_envio_tag.text.upper():
            # Pedido internacional
            stock = 0
            description = "INTERNACIONAL " + description
        elif stock_container:
            stock_text = stock_container.text.split(" ")[0]
            if stock_text == "Agotado":
                stock = 0
            else:
                stock = int(stock_text)
        else:
            stock = -1

        part_number_container = soup.find("span", "sku")

        if part_number_container:
            part_number = part_number_container.text.strip()
        else:
            part_number = None

        picture_containers = soup.findAll("div", "product-image-wrap")
        picture_urls = [
            p.find("a")["href"]
            for p in picture_containers
            if validators.url(p.find("a")["href"])
        ]

        if len(sku) > 50:
            sku = None
        if part_number and len(part_number) > 50:
            part_number = None

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
            part_number=part_number,
        )

        return [p]
