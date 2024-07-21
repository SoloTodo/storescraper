import logging

from bs4 import BeautifulSoup
from storescraper.categories import (
    VIDEO_GAME_CONSOLE,
    MOUSE,
    VIDEO_CARD,
    TABLET,
    PRINTER,
    HEADPHONES,
    NOTEBOOK,
)
from storescraper.stores.mercado_libre_chile import MercadoLibreChile
from storescraper.utils import session_with_proxy


class DacDigital(MercadoLibreChile):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            VIDEO_GAME_CONSOLE,
            VIDEO_CARD,
            TABLET,
            PRINTER,
            HEADPHONES,
            NOTEBOOK,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["computacion/perifericos-pc", MOUSE],
            ["computacion/componentes-pc", VIDEO_CARD],
            ["computacion/tablets-accesorios", TABLET],
            ["computacion/impresion", PRINTER],
            ["electronica-audio-video", HEADPHONES],
            ["computacion/notebooks-accesorios", NOTEBOOK],
            ["consolas-videojuegos", VIDEO_GAME_CONSOLE],
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
                index = str(50 * (page - 1) + 1)
                url_webpage = (
                    "https://www.dacdigital.cl/listado/"
                    "{}/_Desde_{}_NoIndex_True".format(url_extension, index)
                )
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "lxml")
                product_containers = soup.findAll("li", "ui-search-layout__item")
                if not product_containers:
                    if page == 1:
                        logging.warning("Empty category: " + url_extension)
                    break
                for container in product_containers:
                    product_url = (
                        container.find("a", "ui-search-link")["href"]
                        .split("#")[0]
                        .split("?")[0]
                    )
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        return cls._products_for_url_with_custom_price(
            url, category=category, extra_args=extra_args
        )
