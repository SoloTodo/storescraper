from bs4 import BeautifulSoup

from storescraper.categories import (
    HEADPHONES,
    TABLET,
    CELL,
    WEARABLE,
    VIDEO_GAME_CONSOLE,
    STEREO_SYSTEM,
    TELEVISION,
    NOTEBOOK,
)
from .movistar import Movistar
from ..utils import session_with_proxy


class TiendaMovistar(Movistar):
    variations = []
    category_paths = [
        ("celulares", CELL),
        ("outlet/celulares-reacondicionados", CELL),
        ("outlet/tablets", TABLET),
        ("outlet/smartwatch", WEARABLE),
        ("outlet/accesorios", HEADPHONES),
        ("smartwatch", WEARABLE),
        ("tablets", TABLET),
        ("audifonos", HEADPHONES),
        ("gaming/consolas", VIDEO_GAME_CONSOLE),
        ("gaming/accesorios-gamer", HEADPHONES),
        ("smarthome", TELEVISION),
        ("accesorios/parlantes-bluetooth", STEREO_SYSTEM),
        ("notebooks", NOTEBOOK),
    ]

    @classmethod
    def categories(cls):
        return [CELL, TABLET, HEADPHONES, WEARABLE, VIDEO_GAME_CONSOLE, STEREO_SYSTEM]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super(TiendaMovistar, cls).products_for_url(url)

        session = session_with_proxy(extra_args)
        session.headers["Content-Type"] = (
            "application/x-www-form-urlencoded; charset=UTF-8"
        )
        session.headers["x-requested-with"] = "XMLHttpRequest"
        session.headers["referer"] = url
        soup = BeautifulSoup(session.get(url).text, "html5lib")
        form_key = soup.find("input", {"id": "du-form-key"})["value"]
        form_emh = soup.find("input", {"id": "du-form-emh"})["value"]

        for product in products:
            product.key = product.sku
            product.cell_plan_name = None
            product.cell_monthly_payment = None
            payload = f"key={form_key}&emh={form_emh}&sku={product.sku}&tipo_producto=fullprice"
            stock_res = session.post(
                "https://catalogo.movistar.cl/tienda/detalleequipo/ajax/consultastockunificado",
                payload,
            )
            stock_json = stock_res.json()

            if (
                "respuesta" in stock_json
                and stock_json["respuesta"]["detalle"] == "con-stock"
            ):
                product.stock = -1
            else:
                product.stock = 0

        return products
