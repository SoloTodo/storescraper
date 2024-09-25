from decimal import Decimal

from storescraper.categories import (
    AIR_CONDITIONER,
    ALL_IN_ONE,
    CELL,
    HEADPHONES,
    MONITOR,
    NOTEBOOK,
    OVEN,
    REFRIGERATOR,
    STEREO_SYSTEM,
    WASHING_MACHINE,
)
from storescraper.stores.peru_stores import PeruStores


class Oechsle(PeruStores):
    base_url = "https://www.oechsle.pe"
    params = (
        "fq=B:599&O=OrderByScoreDESC&PS=36&sl=cc1f325c-7406-439c-b922-9"
        "b2e850fcc90&cc=36&sm=0"
    )
    product_container_class = "product"

    categories_json = {
        "monitores": MONITOR,
        "soundbar": STEREO_SYSTEM,
        "parlantes y altavoces": STEREO_SYSTEM,
        "parlantes inalámbricos": STEREO_SYSTEM,
        "equipos de sonido": STEREO_SYSTEM,
        "home theater": STEREO_SYSTEM,
        "laptops": NOTEBOOK,
        "celulares": CELL,
        "all in one y computadoras de escritorio": ALL_IN_ONE,
        "refrigeradoras": REFRIGERATOR,
        "lavadoras": WASHING_MACHINE,
        "lavasecas y centros de lavado": WASHING_MACHINE,
        "secadoras": WASHING_MACHINE,
        "hornos microondas": OVEN,
        "aires acondicionados": AIR_CONDITIONER,
        "audífonos on ear": HEADPHONES,
        "audífonos inalámbricos bluetooth": HEADPHONES,
    }
    international_produt_code = "5970"

    @classmethod
    def get_offer_price(cls, session, sku, normal_price, store_seller):
        offer_info = session.get(
            "https://api.retailrocket.net/api/1.0/partn"
            "er/5e6260df97a5251a10daf30d/items/?itemsId"
            "s={}&format=json".format(sku)
        ).json()
        if (
            len(offer_info) != 0
            and offer_info[0]["Params"]["tarjeta"]
            and offer_info[0]["Params"]["tarjeta"] != "0"
            and offer_info[0]["Params"]["seller"] == "oechsle"
        ):
            offer_price = Decimal(offer_info[0]["Params"]["tarjeta"])

            if offer_price > normal_price:
                offer_price = normal_price
        else:
            offer_price = normal_price
        return offer_price
