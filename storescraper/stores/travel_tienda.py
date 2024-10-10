import json
import re
import time
import urllib.parse
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    CELL,
    PRINTER,
    WEARABLE,
    TELEVISION,
    STEREO_SYSTEM,
    NOTEBOOK,
    MONITOR,
    TABLET,
    HEADPHONES,
    MOUSE,
    GAMING_CHAIR,
    REFRIGERATOR,
    OVEN,
    AIR_CONDITIONER,
    VIDEO_GAME_CONSOLE,
    WASHING_MACHINE,
    VACUUM_CLEANER,
    SPACE_HEATER,
    DISH_WASHER,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class TravelTienda(StoreWithUrlExtensions):
    url_extensions = [
        ("3842720512", CELL),  # Tech > Telefonía > Smartphones
        ("816923966", WEARABLE),  # Tech > Telefonía > Smartwatch
        ("2722336774", TELEVISION),  # Tech > TV > Televisores
        ("2234300147", STEREO_SYSTEM),  # Tech > TV > Sistemas de Sonido TV
        ("2934181475", TABLET),  # Tech > Comp. > Tablets
        ("3415774358", NOTEBOOK),  # Tech > Comp. > Notebook
        ("3213133197", PRINTER),  # Tech > Computación > Domótica & Acc.
        ("714969430", GAMING_CHAIR),  # Tech > Gamer > Sillas y Escritorios
        ("1226813193", HEADPHONES),  # Tech > Gamer > Audífonos Gamer
        ("2547146328", MOUSE),  # Tech > Gamer > Periféricos
        ("2881216585", VIDEO_GAME_CONSOLE),  # Tech > Gamer > Consolas y Ac
        ("3121709090", HEADPHONES),  # Tech > Audio > Audífonos
        ("326296390", STEREO_SYSTEM),  # Tech > Audio > Audio Portátil
        ("742795275", STEREO_SYSTEM),  # Tech > Audio > Soundbar
        ("1095159098", STEREO_SYSTEM),  # Tech > Audio Hi-Fi > Parlantes y
        ("3555399911", STEREO_SYSTEM),  # Tech > Audio Hi-Fi > Stereo
        ("1379171641", STEREO_SYSTEM),  # Tech > Audio Hi-Fi > Subwoofer y
        ("4064311224", STEREO_SYSTEM),  # Tech > Audio
        ("1479054651", STEREO_SYSTEM),  # Tech > Audio HiFi
        ("2074305120", REFRIGERATOR),  # Home > Electrohogar > Refrigeración
        ("1073939402", OVEN),
        ("779019428", OVEN),
        ("110098225", AIR_CONDITIONER),
        ("4005764418", WASHING_MACHINE),
        ("3421645721", PRINTER),  # Tecnología > Computación > Accesorios de Computacion
        ("375810843", MONITOR),  # Tecnología > Computación > Monitores
        ("955484130", VACUUM_CLEANER),  # Aspirado y limpieza
        # ("1189841113", VACUUM_CLEANER),  # Aspirado y limpieza
        ("312008500", SPACE_HEATER),  # Calefaccion
        # ("1445819056", DISH_WASHER),  # Lavavajillas
        ("2661527844", DISH_WASHER),  # Lavavajillas
        # ("1318662286", OVEN),  # Empotrados
        ("1864719901", OVEN),  # Empotrados
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        url_webpage = (
            "https://tienda.travel.cl/ccstore/v1/assembler/"
            "pages/Default/osf/catalog/_/N-{}?Nrpp=1000"
            "&Nr=AND%28sku.availabilityStatus%3AINSTOCK%29"
            "".format(url_extension)
        )
        response = session.get(url_webpage)
        json_data = response.json()

        if not json_data["results"]["records"]:
            # Consider empty categories to be errors because Travel
            # Tienda has changed category ids in the past
            raise Exception("Empty category: ", url_extension)

        for product_entry in json_data["results"]["records"]:
            product_path = product_entry["attributes"]["product.route"][0]
            product_url = "https://tienda.travel.cl" + product_path
            print(product_url)
            product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        # print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        script_tag = soup.find("script", {"data-name": "occ-structured-data"})

        if not script_tag:
            if extra_args:
                retries = extra_args.get("retries", 5)
                if retries > 0:
                    retries -= 1
                    extra_args["retries"] = retries
                    time.sleep(2)
                    return cls.products_for_url(url, category, extra_args)
                else:
                    return []
            else:
                extra_args = {"retries": 5}
                time.sleep(2)
                return cls.products_for_url(url, category, extra_args)

        data = soup.find("body").find("script").text

        data_clean = urllib.parse.unquote(
            re.search(r"window.state = JSON.parse\(decodeURI\((.+)\)\)", data).groups()[
                0
            ]
        )
        page_json = json.loads(data_clean[1:-1])
        publication_id = page_json["clientRepository"]["context"]["request"][
            "productId"
        ]
        publication_entry = page_json["catalogRepository"]["products"][publication_id]
        products = []
        skus_data = page_json["catalogRepository"]["skus"]

        for sku, sku_data in skus_data.items():
            name = sku_data["displayName"]

            prices_dict = page_json["priceRepository"]["skus"][sku]

            if not prices_dict["salePrice"] and not prices_dict["listPrice"]:
                continue

            normal_price = Decimal(prices_dict["salePrice"] or prices_dict["listPrice"])
            offer_price = normal_price

            # This is very sus, the offer price appears in the publication
            # entry, not in the sku entry
            if publication_entry["listPrices"]["tiendaBancoDeChile"]:
                offer_price = Decimal(
                    publication_entry["listPrices"]["tiendaBancoDeChile"]
                )

            if "salePrices" in publication_entry:
                if publication_entry["salePrices"]["tienda"]:
                    normal_price = Decimal(publication_entry["salePrices"]["tienda"])
                if publication_entry["salePrices"]["tiendaBancoDeChile"]:
                    offer_price = Decimal(
                        publication_entry["salePrices"]["tiendaBancoDeChile"]
                    )

            if len(skus_data) > 1:
                # All the SKUs share the same part number according to the
                # webpage, which is suspicious if there is more than one
                part_number = None
            else:
                part_number = publication_entry.get("x_codigoProveedor", None)

            picture_urls = [
                "https://tienda.travel.cl" + picture.replace(" ", "%20")
                for picture in publication_entry["fullImageURLs"]
            ]

            print(page_json["inventoryRepository"]["skus"][sku])
            stock = page_json["inventoryRepository"]["skus"][sku]["default"].get(
                "orderableQuantity", 0
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
                part_number=part_number,
            )
            products.append(p)

        return products
