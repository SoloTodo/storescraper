import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    MONITOR,
    HEADPHONES,
    STEREO_SYSTEM,
    MOUSE,
    NOTEBOOK,
    TABLET,
    GAMING_CHAIR,
    VIDEO_GAME_CONSOLE,
    GAMING_DESK,
    CELL,
    COMPUTER_CASE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import cf_session_with_proxy, remove_words


class LoiChile(StoreWithUrlExtensions):
    CURRENCY = "CLP"
    IMAGE_DOMAIN = "d660b7b9o0mxk"

    # URL Extensions are in a input with name "categ_id" in category pages
    url_extensions = [
        ["16", CELL],
        ["17", TABLET],
        ["10", MONITOR],
        ["1", HEADPHONES],
        ["25", STEREO_SYSTEM],
        ["2", NOTEBOOK],
        ["23", MOUSE],
        ["208", COMPUTER_CASE],
        ["207", VIDEO_GAME_CONSOLE],
        ["154", GAMING_CHAIR],
        ["155", GAMING_DESK],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = cf_session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        )
        session.headers["Cookie"] = (
            "cf_clearance=nHt8.nUwp8rNLsuEHMb4NGw620W1L1k8P8nzZgT3bLM-1729174456-1.2.1.1-3IOKpzlfDUTKw7AEcD0yKlc7ikhg7ZAjCn9i2tBglyxu.vUwrpQPBlPBNeB1G0UVWjTqUbTWATwpYV5DPhHwe1BOlL4SYos7wyD2Php1A2cLfTDGesvTFmme.qTgvxnc4lMOtWd29v9PqWpjuQI4oqW3G7BPQYElyucX9nppKHi_1VLPASiFao1fJ0RCEC8yuvovSvhb_KIE07HGW3CgnexYbqyHrEJl9aWyXqGynAKoMo23OzNlQn73rDmFdPfuVrU9vWPqaUSFEFBjUFBkDBmOzlIxReK0kPez8AldCDDcgQ7zyHBmw5zDrD4px4X2ZSLDJsO4oZwNH4urBWDvKXqd1xYfar6O68TsND91UtHIu0Acl2kq8yU5fZOFDW_2p33nQx8Ke1UNqouEyRh7DjSHzSizRSf5R.iMrBjp.a.mVZA5LLaxpx9PV3E28D1I;"
        )
        products_urls = []
        page_size = 50
        page = 0

        while True:
            if page > 10:
                raise Exception("Page overflow")
            url_webpage = (
                "https://loichile.cl/index.php?ctrl=productos&"
                "act=categoriasReact&categ_id={}&cantidad={}"
                "".format(url_extension, page * page_size)
            )
            print(url_webpage)
            response = session.get(url_webpage)
            product_entries = response.json()["listaProductos"]

            if not product_entries:
                if page == 0:
                    logging.warning("Empty category: " + url_extension)
                break

            for product_entry in product_entries:
                product_path = product_entry["urlseo"]
                products_urls.append("https://loichile.cl/" + product_path)
            page += 1
        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = cf_session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        )
        session.headers["Cookie"] = (
            "cf_clearance=nHt8.nUwp8rNLsuEHMb4NGw620W1L1k8P8nzZgT3bLM-1729174456-1.2.1.1-3IOKpzlfDUTKw7AEcD0yKlc7ikhg7ZAjCn9i2tBglyxu.vUwrpQPBlPBNeB1G0UVWjTqUbTWATwpYV5DPhHwe1BOlL4SYos7wyD2Php1A2cLfTDGesvTFmme.qTgvxnc4lMOtWd29v9PqWpjuQI4oqW3G7BPQYElyucX9nppKHi_1VLPASiFao1fJ0RCEC8yuvovSvhb_KIE07HGW3CgnexYbqyHrEJl9aWyXqGynAKoMo23OzNlQn73rDmFdPfuVrU9vWPqaUSFEFBjUFBkDBmOzlIxReK0kPez8AldCDDcgQ7zyHBmw5zDrD4px4X2ZSLDJsO4oZwNH4urBWDvKXqd1xYfar6O68TsND91UtHIu0Acl2kq8yU5fZOFDW_2p33nQx8Ke1UNqouEyRh7DjSHzSizRSf5R.iMrBjp.a.mVZA5LLaxpx9PV3E28D1I;"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        name = (
            soup.find("h1", "nombre-producto-info")
            .text.replace("\t", "")
            .replace("\n", "")
        )
        sku = soup.find("span", {"id": "idProducto"}).text

        price_tag = soup.find("div", {"id": "contenedor_precio_detalle_producto"})
        if price_tag:
            price = Decimal(price_tag["data-precio"].replace(",", ".")).quantize(0)
        else:
            price_tag = soup.find("p", "hotsale-precio-hotsale").find("span")
            price = Decimal(remove_words(price_tag.text.replace("USD", "")))

        picture_urls = []

        picture_response = session.get(
            f"https://loi.com.uy/index.php?ctrl=productos&urlseo=smart-tv-lg-4k-43ur7800psb"
        )

        for picture in picture_response.json()["multimedia"]:
            picture_urls.append(
                f"https://{cls.IMAGE_DOMAIN}.cloudfront.net/{picture['url']}"
            )

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            cls.CURRENCY,
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
