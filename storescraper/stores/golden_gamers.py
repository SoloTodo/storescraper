import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    HEADPHONES,
    MOTHERBOARD,
    PROCESSOR,
    VIDEO_CARD,
    COMPUTER_CASE,
    RAM,
    GAMING_CHAIR,
    MOUSE,
    KEYBOARD,
    MONITOR,
    NOTEBOOK,
    CPU_COOLER,
    POWER_SUPPLY,
    MICROPHONE,
    TABLET,
    STEREO_SYSTEM,
    SOLID_STATE_DRIVE,
    CASE_FAN,
    VIDEO_GAME_CONSOLE,
    CELL,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class GoldenGamers(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            COMPUTER_CASE,
            RAM,
            GAMING_CHAIR,
            MOUSE,
            KEYBOARD,
            MONITOR,
            NOTEBOOK,
            CPU_COOLER,
            POWER_SUPPLY,
            MICROPHONE,
            TABLET,
            STEREO_SYSTEM,
            SOLID_STATE_DRIVE,
            CASE_FAN,
            VIDEO_GAME_CONSOLE,
            CELL,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["notebooks", NOTEBOOK],
            ["silla-gamer", GAMING_CHAIR],
            ["monitores", MONITOR],
            ["monitores-1", MONITOR],
            ["teclados", KEYBOARD],
            ["mouse-gamer", MOUSE],
            ["tablets", TABLET],
            ["audifonos", HEADPHONES],
            ["audifonos-dia-del-nino", HEADPHONES],
            ["accesorios/tipo-de-producto_microfonos", MICROPHONE],
            ["accesorios/tipo-de-producto_parlantes", STEREO_SYSTEM],
            ["accesorios/tipo-de-producto_refrigeracion", CASE_FAN],
            ["componentes/tipo-de-producto_almacenamiento", SOLID_STATE_DRIVE],
            ["componentes/tipo-de-producto_cpu", PROCESSOR],
            ["componentes/tipo-de-producto_fuente-de-poder", POWER_SUPPLY],
            ["componentes/tipo-de-producto_gabinete", COMPUTER_CASE],
            ["componentes/tipo-de-producto_memoria-ram", RAM],
            ["componentes/tipo-de-producto_placa-madre", MOTHERBOARD],
            ["componentes/tipo-de-producto_refrigeracion", CPU_COOLER],
            ["componentes/tipo-de-producto_tarjeta-de-video", VIDEO_CARD],
            ["consolas", VIDEO_GAME_CONSOLE],
            ["celulares", CELL],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 15:
                    raise Exception("page overflow: " + url_extension)
                url_webpage = (
                    "https://goldengamers.cl/collections/"
                    "{}?page={}".format(url_extension, page)
                )
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "lxml")
                products_tag = soup.find("div", "collection-row")

                if not products_tag:
                    raise Exception(data)

                product_containers = products_tag.findAll(
                    "div", "collection-products-wrapper"
                )

                if not product_containers:
                    if page == 1:
                        logging.warning("Empty category: " + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find("a")["href"]
                    product_urls.append("https://goldengamers.cl" + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        product_container = soup.find("div", {"id": "parent"})

        if not product_container:
            raise Exception(response.text)

        name = product_container.find("h1", "product-item-caption-title").text
        sku = product_container.find("span", "shopify-product-reviews-badge")["data-id"]
        stock_container = (
            product_container.find("div", {"id": "variant-inventory"})
            .text.strip()
            .split()[2]
        )
        if stock_container.isnumeric():
            stock = int(stock_container)
        else:
            stock = 0
        offer_price = Decimal(
            remove_words(
                product_container.find("ul", "product-item-caption-price")
                .find("li", "product-item-caption-price-current")
                .text.replace("CLP", "")
            )
        )

        if not offer_price:
            return []

        normal_price = offer_price * Decimal("1.03")

        picture_urls = [
            "https:" + tag["src"].replace("_small", "").split("?")[0]
            for tag in product_container.find(
                "div", "swiper-horiz-" "thumbnails-main-container"
            ).findAll("img")
        ]

        description = html_to_markdown(
            str(soup.find("div", "product-item-caption-desc"))
        )

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            "CLP",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
