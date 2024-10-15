import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    NOTEBOOK,
    PRINTER,
    MONITOR,
    HEADPHONES,
    KEYBOARD,
    WEARABLE,
    ALL_IN_ONE,
    TABLET,
    CELL,
    GAMING_CHAIR,
    UPS,
    SOLID_STATE_DRIVE,
    POWER_SUPPLY,
    COMPUTER_CASE,
    RAM,
    PROCESSOR,
    VIDEO_CARD,
    MOTHERBOARD,
    EXTERNAL_STORAGE_DRIVE,
    MOUSE,
    STEREO_SYSTEM,
    VIDEO_GAME_CONSOLE,
    CPU_COOLER,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class NotebooksYa(StoreWithUrlExtensions):
    url_extensions = [
        ["apple-watch", WEARABLE],
        ["ipad", TABLET],
        ["imac", ALL_IN_ONE],
        ["macbooks", NOTEBOOK],
        ["accesorios-gamer/?filter_producto-gamer=tarjeta-de-video", VIDEO_CARD],
        [
            "accesorios-gamer/?filter_producto-almacenamiento=tarjeta-de-memoria",
            EXTERNAL_STORAGE_DRIVE,
        ],
        ["audifonos-gamer", HEADPHONES],
        ["monitores-gamer", MONITOR],
        ["portatiles-ya/notebooks-ya/notebooks-gamer", NOTEBOOK],
        ["sillas-gamer", GAMING_CHAIR],
        ["teclados-gamer", KEYBOARD],
        ["notebooks-ya", NOTEBOOK],
        ["tablets", TABLET],
        ["celulares-ya", CELL],
        ["computadores-ya/?filter_producto-computadores=all-in-one", ALL_IN_ONE],
        ["computadores-ya/?filter_producto-computadores=imac", ALL_IN_ONE],
        ["monitores-ya", MONITOR],
        [
            "almacenamiento-ya",
            SOLID_STATE_DRIVE,
        ],
        ["audifonos-ya", HEADPHONES],
        ["teclados-mouse-ya", MOUSE],
        ["relojes-ya", WEARABLE],
        ["sillas-ya", GAMING_CHAIR],
        [
            "partes-y-piezas-ya/?filter_producto-partes-y-piezas=" "fuente-de-poder",
            POWER_SUPPLY,
        ],
        [
            "partes-y-piezas-ya/?filter_producto-partes-y-piezas=gabinetes",
            COMPUTER_CASE,
        ],
        [
            "partes-y-piezas-ya/?filter_producto-partes-y-piezas="
            "memoria-ram-para-laptops",
            RAM,
        ],
        [
            "partes-y-piezas-ya/?filter_producto-partes-y-piezas="
            "memoria-ram-para-pc",
            RAM,
        ],
        [
            "partes-y-piezas-ya/?filter_producto-partes-y-piezas=placa-madre",
            MOTHERBOARD,
        ],
        ["partes-y-piezas-ya/?filter_producto-partes-y-piezas=procesadores", PROCESSOR],
        [
            "partes-y-piezas-ya/?filter_producto-partes-y-piezas=" "tarjeta-de-video",
            VIDEO_CARD,
        ],
        ["impresion-ya", PRINTER],
        ["audio-y-video-ya/?filter_producto-audio-y-video=audifonos", HEADPHONES],
        [
            "audio-y-video-ya/?filter_producto-audio-y-video=parlante-portatil",
            STEREO_SYSTEM,
        ],
        ["audio-y-video-ya/?filter_producto-audio-y-video=sound-bar", STEREO_SYSTEM],
        ["ups-ya/?filter_producto-ups=ups", UPS],
        ["consolas-y-controles", VIDEO_GAME_CONSOLE],
        [
            "partes-y-piezas-ya/?filter_producto-partes-y-piezas=refrigeracion",
            CPU_COOLER,
        ],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        session.headers["X-Requested-With"] = "XMLHttpRequest"
        product_urls = []
        page = 1
        done = False
        while not done:
            if page > 20:
                raise Exception("page overflow: " + url_extension)

            url_components = url_extension.split("?")

            if len(url_components) > 1:
                query = url_components[1]
            else:
                query = ""

            url_webpage = (
                "https://notebooksya.cl/product-category/{}/"
                "page/{}/?load_posts_only=1&{}"
            ).format(url_extension, page, query)

            print(url_webpage)

            response = session.get(url_webpage)

            if response.status_code == 404:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break

            soup = BeautifulSoup(response.text, "lxml")

            template_tag = soup.find("script", {"type": "text/template"})
            if template_tag:
                template_soup = BeautifulSoup(json.loads(template_tag.text), "lxml")
                product_containers = template_soup.findAll("li", "product")
            else:
                product_containers = soup.findAll("li", "product")

            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break

            for container in product_containers:
                product_url = container.find("a")["href"]
                if product_url in product_urls:
                    return product_urls
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        raw_soup = BeautifulSoup(response.text, "lxml")
        content_tag = raw_soup.find("script", {"type": "text/template"})

        if not content_tag:
            return []

        soup = BeautifulSoup(json.loads(content_tag.text), "lxml")

        name = soup.find("h2").text.strip()
        key = soup.find("a", "single_add_to_wishlist")["data-product-id"]

        qty_input = soup.find("input", "qty")

        if not qty_input:
            return []

        if "max" in qty_input.attrs:
            if qty_input["max"]:
                stock = int(qty_input["max"])
            else:
                stock = -1
        else:
            stock = 1
        price_tags = soup.findAll("span", "woocommerce-Price-amount")
        assert len(price_tags) in [2, 3]

        offer_price = Decimal(remove_words(price_tags[-2].text))
        normal_price = Decimal(remove_words(price_tags[-1].text))
        sku = soup.find("span", "sku").text.strip()

        picture_containers = soup.find("div", "product-image-slider").findAll(
            "div", "img-thumbnail"
        )
        picture_urls = []

        for picture in picture_containers:
            picture_url = picture.find("img")["href"]
            picture_urls.append(picture_url)

        description = html_to_markdown(str(soup.find("div", "description")))

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
