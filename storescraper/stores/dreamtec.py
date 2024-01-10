import re
from decimal import Decimal
from storescraper.categories import (
    ALL_IN_ONE,
    GAMING_CHAIR,
    HEADPHONES,
    MONITOR,
    NOTEBOOK,
    PRINTER,
    STEREO_SYSTEM,
    TABLET,
    TELEVISION,
    VIDEO_GAME_CONSOLE,
    MOUSE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown, check_ean13


class Dreamtec(StoreWithUrlExtensions):
    url_extensions = [
        ["accesorios", MOUSE],
        ["audifonos", HEADPHONES],
        ["audio", STEREO_SYSTEM],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["monitores", MONITOR],
        ["notebooks", NOTEBOOK],
        ["sillas-gamer", GAMING_CHAIR],
        ["all-in-one", ALL_IN_ONE],
        ["impresoras", PRINTER],
        ["macbook", NOTEBOOK],
        ["parlantes", STEREO_SYSTEM],
        ["smart-tv", TELEVISION],
        ["soundbar", STEREO_SYSTEM],
        ["tablets", TABLET],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            if page > 20:
                raise Exception("Page overflow")

            url_webpage = "https://dreamtec.cl:3000/categoria/{}?page={}".format(
                url_extension, page
            )
            print(url_webpage)
            response = session.get(url_webpage)
            products_json = response.json()["results"]

            if not products_json:
                break

            for container in products_json:
                product_url = "https://www.dreamtec.cl/" + container["slug"]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        slug = re.search(r"https://www.dreamtec.cl/(.+)$", url).groups()[0]
        endpoint = "https://dreamtec.cl:3000/slug/" + slug
        response = session.get(endpoint)
        product_data = response.json()["results"][0]
        name = product_data["nombre"]
        description = html_to_markdown(product_data["descripcion"])
        sku = product_data["sku"]
        normal_price = Decimal(product_data["precio"])
        offer_price = Decimal(product_data["precio_descuento"])
        part_number = product_data["pn"]
        stock = product_data["stock"]

        ean_candidate = product_data["upc"] or ""
        if len(ean_candidate) == 12:
            ean_candidate = "0" + ean_candidate
        if check_ean13(ean_candidate):
            ean = ean_candidate
        else:
            ean = None

        picture_urls = [
            "https://dreamtec.cl/" + product_data[tag].replace(" ", "%20")
            for tag in ["foto_1", "foto_2", "foto_3"]
            if tag in product_data
        ]

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
            part_number=part_number,
            picture_urls=picture_urls,
            description=description,
            ean=ean,
        )
        return [p]
