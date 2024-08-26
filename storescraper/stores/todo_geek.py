from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import (
    MONITOR,
    PROCESSOR,
    STEREO_SYSTEM,
    VIDEO_CARD,
    NOTEBOOK,
    GAMING_CHAIR,
    VIDEO_GAME_CONSOLE,
    WEARABLE,
    CELL,
    KEYBOARD,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class TodoGeek(StoreWithUrlExtensions):
    url_extensions = [
        ["procesadores", PROCESSOR],
        ["tarjetas-graficas", VIDEO_CARD],
        ["monitores", MONITOR],
        ["parlantes-inteligentes", STEREO_SYSTEM],
        ["sillas-gamer", GAMING_CHAIR],
        ["watches", WEARABLE],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["celulares", CELL],
        ["Teclados", KEYBOARD],
        ["notebooks", NOTEBOOK],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://todogeek.cl/collections/{}?" "page={}".format(
                url_extension, page
            )
            res = session.get(url_webpage)
            soup = BeautifulSoup(res.text, "lxml")
            product_containers = soup.findAll("product-card")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("h3", "product-card_title").find("a")[
                    "href"
                ]
                product_urls.append("https://todogeek.cl" + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        match = re.search(r'"delivery__app_setting": (.+),', response.text)
        json_data = json.loads(match.groups()[0])
        order_ready_day_range = json_data["main_delivery_setting"][
            "order_delivery_day_range"
        ]
        max_day = max(order_ready_day_range)

        category_tags = soup.find("span", text="Categoria: ").parent.findAll("a")
        assert category_tags

        state_tag = soup.find("p", "product-state")

        if state_tag:
            state_tag_text = state_tag.text.upper()
            if "NUEVO" in state_tag_text:
                condition = "https://schema.org/NewCondition"
            elif "USADO" in state_tag_text:
                condition = "https://schema.org/UsedCondition"
            elif "REACONDICIONADO" in state_tag_text:
                condition = "https://schema.org/RefurbishedCondition"
            else:
                raise Exception("Invalid condition: " + state_tag_text)
        else:
            condition = "https://schema.org/RefurbishedCondition"

        if max_day > 2:
            a_pedido = True
        else:
            for tag in category_tags:
                if "ESPERALO" in tag.text.upper() or "ESPERALO" in tag["href"].upper():
                    a_pedido = True
                    break
                if "RESERVA" in tag.text.upper() or "RESERVA" in tag["href"].upper():
                    a_pedido = True
                    break
            else:
                a_pedido = False

        picture_urls = []

        json_data = soup.findAll("script", {"type": "application/ld+json"})
        picture_urls = json.loads(json_data[0].text)["offers"]["image"]
        product_data = [
            json.loads(data.text)
            for data in json_data
            if json.loads(data.text)["@type"] == "Product"
            and "description" in json.loads(data.text)
        ][0]
        description = html_to_markdown(product_data["description"])
        products = []
        offers = product_data["offers"]
        for offer in offers:
            key = offer["url"].split("?variant=")[1]
            sku = offer.get("sku", None)
            name = product_data["name"]

            if len(offers) > 1:
                name += f" ({offer['name']})"

            offer_price = Decimal(offer["price"]).quantize(0)
            normal_price = (offer_price * Decimal("1.035")).quantize(0)

            if a_pedido or "RESERVA" in description.upper() or "VENTA" in name.upper():
                stock = 0
            elif offer["availability"] == "https://schema.org/InStock":
                stock = -1
            else:
                stock = 0

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
                condition=condition,
            )
            products.append(p)
        return products
