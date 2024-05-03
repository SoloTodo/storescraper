import json
import logging
import random
import re
import urllib

import time

from collections import defaultdict
from decimal import Decimal

import validators
from bs4 import BeautifulSoup
from html import unescape

from curl_cffi.requests import RequestsError
from dateutil.parser import parse
from requests import TooManyRedirects
from curl_cffi import requests

from storescraper.categories import *
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import (
    remove_words,
    html_to_markdown,
    session_with_proxy,
)
from storescraper import banner_sections as bs


class Falabella(Store):
    preferred_discover_urls_concurrency = 3
    preferred_products_for_url_concurrency = 20
    store_and_subdomain = None
    seller = [
        {"id": "FALABELLA", "section_prefix": "RETAIL", "include_in_fast_mode": True},
        {"id": None, "section_prefix": "GRUPO", "include_in_fast_mode": False},
    ]
    seller_blacklist = ["SODIMAC", "TOTTUS"]
    banners_base_url = "https://www.falabella.com/falabella-cl/{}"
    banners_sections_data = [
        [bs.HOME, "Home", bs.SUBSECTION_TYPE_HOME, ""],
        # # CATEGORY PAGES # #
        [
            bs.REFRIGERATION,
            "Electrohogar-Refrigeradores",
            bs.SUBSECTION_TYPE_CATEGORY_PAGE,
            "category/cat3205/Refrigeradores?isLanding=true",
        ],
        [
            bs.AUDIO,
            "Audio",
            bs.SUBSECTION_TYPE_CATEGORY_PAGE,
            "category/cat2005/Audio?isLanding=true",
        ],
        [
            bs.CELLS,
            "Telefonía-Celulares y Teléfonos",
            bs.SUBSECTION_TYPE_CATEGORY_PAGE,
            "category/cat2018/Celulares-y-Telefonos?isLanding=true",
        ],
        # # MOSAICS ##
        [
            bs.LINEA_BLANCA_FALABELLA,
            "Electro y Tecnología-Línea Blanca",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat7090035/Linea-Blanca?isPLP=1",
        ],
        [
            bs.REFRIGERATION,
            "Refrigeradores-No Frost",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat4074/No-Frost",
        ],
        [
            bs.REFRIGERATION,
            "Refrigeradores-Side by Side",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat4091/Side-by-Side",
        ],
        [
            bs.WASHING_MACHINES,
            "Lavadoras",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat3136/Lavadoras",
        ],
        [
            bs.WASHING_MACHINES,
            "Lavadoras-Lavadoras",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat4060/Lavadoras",
        ],
        [
            bs.WASHING_MACHINES,
            "Lavadoras-Lavadoras-Secadoras",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat1700002/Lavadoras-Secadoras",
        ],
        [
            bs.WASHING_MACHINES,
            "Lavadoras-Secadoras",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat4088/Secadoras",
        ],
        [
            bs.WASHING_MACHINES,
            " Lavadoras-Lavadoras Doble Carga",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat11400002/Lavadoras-Doble-Carga",
        ],
        [
            bs.TELEVISIONS,
            "Tecnología-TV",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat1012/TV?isPLP=1",
        ],
        [
            bs.TELEVISIONS,
            "Televisores LED",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat7190148/Televisores-LED",
        ],
        [
            bs.TELEVISIONS,
            "LEDs menores a 50 pulgadas",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat11161614/LEDs-menores-a-50-pulgadas",
        ],
        [
            bs.TELEVISIONS,
            "LEDs entre 50 - 55 pulgadas",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat11161675/LEDs-entre-50---55-pulgadas",
        ],
        [
            bs.TELEVISIONS,
            "LEDs sobre 55 pulgadas",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat11161679/LEDs-sobre-55-pulgadas",
        ],
        [
            bs.TELEVISIONS,
            "TV-LED",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat2850014/LED",
        ],
        [
            bs.TELEVISIONS,
            "TV-Smart TV",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat3040054/Smart-TV",
        ],
        [
            bs.TELEVISIONS,
            "TV-4K UHD",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat3990038/4K-UHD",
        ],
        [
            bs.TELEVISIONS,
            "TV-Televisores OLED",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat2850016/Televisores-OLED",
        ],
        [
            bs.TELEVISIONS,
            "TV-Pulgadas Altas",
            bs.SUBSECTION_TYPE_MOSAIC,
            'category/cat12910024/Televisores-LED-Desde-65"',
        ],
        [
            bs.AUDIO,
            "Audio-Soundbar y Home Theater",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat2045/Home-Theater",
        ],
        [
            bs.AUDIO,
            "Home Theater",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat3050040/Home-Theater",
        ],
        [
            bs.AUDIO,
            "Soundbar",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat1700004/Soundbar",
        ],
        [
            bs.AUDIO,
            "Minicomponente",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat70018/Minicomponente",
        ],
        [
            bs.AUDIO,
            "Audio-Equipos de Música y Karaokes",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat3091/?mkid=CA_P2_MIO1_024794",
        ],
        [
            bs.AUDIO,
            "Audio-Hi-Fi",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat3203/Hi-Fi",
        ],
        [
            bs.AUDIO,
            "Audio",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat2005/Audio?isPLP=1",
        ],
        [
            bs.CELLS,
            "Smartphones",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat720161/Smartphones",
        ],
        [
            bs.CELLS,
            "Electro y Tecnología-Teléfonos",
            bs.SUBSECTION_TYPE_MOSAIC,
            "category/cat2018/Telefonos?isPLP=1",
        ],
    ]

    zones = (
        "PCL2281,ZL_CERRILLOS,PCL1135,3045,PCL1486,FALABELLA_FBY_SDD,"
        "PCL2269,LOSC,PCL540,2020,PCL1186,FEDEX_RM_URB,PCL2520,PCL1336,"
        "CHILEXPRESS_8,PCL1839,BX_R13_BASE,PCL226,SCD9039_FLEX,PCL105,"
        "HUB_SALIDA_DIRECTA_RM,PCL2120,PCL1923,PCL2441,1234,PCL1223,"
        "FBY_BT_CTT,PCL2661,130617,PCL25,PCL2442,BLUE_RM_URBANO,PCL115,"
        "RM,PCL94,PCL2511,PCL108,13,PCL861,CHILE_INTERNATIONAL,PCL1364,"
        "PCL109,PCL184"
    )

    category_paths = [
        [
            "cat720161",
            [CELL],
            "Home > Tecnología-Telefonía > Celulares y Teléfonos > Smartphones",
            1,
        ],
        [
            "cat1280018",
            [CELL],
            "Home > Tecnología-Telefonía > Celulares y Telé"
            "fonos > Celulares Básicos",
            1,
        ],
        ["cat1640002", [HEADPHONES], "Home > Tecnología-Audio > Audífonos", 1],
        [
            "cat70037",
            [MEMORY_CARD],
            "Home > Tecnología-Telefonía > Accesorios "
            "Celulares > Tarjetas de Memoria",
            1,
        ],
        ["cat4290064", [WEARABLE], "Home > Tecnología-Wearables > Smartband", 1],
        ["cat4290063", [WEARABLE], "Home > Tecnología-Wearables > SmartWatch", 1],
        [
            "cat429001",
            [WEARABLE],
            "Home > Tecnología-Wearables > SmartWatch Infantil",
            1,
        ],
        ["cat1012", [TELEVISION], "Home > Tecnología-TV y Video", 0],
        ["cat7190148", [TELEVISION], "Home > Tecnología-TV > Smart TV", 1],
        [
            "cat7190148",
            [TELEVISION],
            'Home > Tecnología-TV > Smart tv entre 50" - 55"',
            1,
            {"f.variant.custom.Tama%C3%B1o_de_la_pantalla": "50::55"},
        ],
        [
            "cat7190148",
            [TELEVISION],
            'Home > Tecnología-TV > Smart tv sobre 55"',
            1,
            {
                "f.derived.product.Tamano_de_la_pantalla": "58::60::65::70::75::77::85::86::98"
            },
        ],
        [
            "cat7190148",
            [TELEVISION],
            'Home > Tecnología-TV > Smart tv menores a 50"',
            1,
            {
                "f.variant.custom.Tama%C3%B1o_de_la_pantalla": "1::20::24::32::39::40::42::43::48"
            },
        ],
        ["cat2070", [PROJECTOR], "Home > Tecnología-TV > Proyectores", 1],
        ["cat2005", [STEREO_SYSTEM], "Home > Tecnología-Audio", 0],
        [
            "cat3091",
            [STEREO_SYSTEM],
            "Home > Tecnología-Audio > Equipos de Música y Karaokes",
            1,
        ],
        ["cat3203", [STEREO_SYSTEM], "Home > Tecnología-Audio > Hi-Fi", 1],
        [
            "cat3171",
            [STEREO_SYSTEM],
            "Home > Tecnología-Audio > Parlantes Bluetooth",
            1,
        ],
        [
            "cat2045",
            [STEREO_SYSTEM],
            "Home > Tecnología-Audio > Soundbar y Home Theater",
            1,
        ],
        [
            "cat3155",
            [MOUSE],
            "Home > Tecnología-Computadores > Accesorios Computación > Mouse",
            1,
        ],
        [
            "cat2370002",
            [KEYBOARD],
            "Home > Tecnología-Computadores > Accesorios Computación > Teclados",
            1,
        ],
        [
            "cat3239",
            [STEREO_SYSTEM],
            "Home > Tecnología-Computadores > Accesor"
            "ios Computación > Parlantes y Subwoofer",
            1,
        ],
        ["cat40051", [ALL_IN_ONE], "Home > Tecnología-Computadores > All in one", 1],
        [
            "cat3087",
            [EXTERNAL_STORAGE_DRIVE],
            "Home > Tecnología-Computadores > Almacenamiento > Discos duros",
            1,
        ],
        [
            "cat3177",
            [USB_FLASH_DRIVE],
            "Home > Tecnología-Computación > Almacenamiento > Pendrives",
            1,
        ],
        [
            "cat1820006",
            [PRINTER],
            "Home > Tecnología-Computadores > Impresoras"
            " y Tintas > Impresoras Multifuncionales",
            1,
        ],
        [
            "cat1820004",
            [PRINTER],
            "Home > Tecnología-Computadores > Impresoras y Tintas > Impresoras",
            1,
        ],
        [
            "cat6680042",
            [PRINTER],
            "Home > Tecnología-Computadores > Impresoras"
            " y Tintas > Impresoras Tradicionales",
            1,
        ],
        [
            "cat11970007",
            [PRINTER],
            "Home > Tecnología-Computadores > Impresora"
            "s y Tintas > Impresoras Láser",
            1,
        ],
        ["cat2062", [MONITOR], "Home > Tecnología-Computadores > Monitores", 1],
        ["cat70057", [NOTEBOOK], "Home > Tecnología-Computadores > Notebooks", 1],
        ["cat7230007", [TABLET], "Home > Tecnología-Computadores > Tablets", 1],
        [
            "cat4930009",
            [HEADPHONES],
            "Home > Tecnología-Computadores > Accesorios gamer > Audífonos gamer",
            1,
        ],
        [
            "CATG19011",
            [GAMING_CHAIR],
            "Home > Tecnología-Computadores > Accesorios gamer > Sillas gamer",
            1,
        ],
        [
            "CATG19008",
            [KEYBOARD],
            "Home > Tecnología-Computadores > Accesorios gamer > Tecaldos gamer",
            1,
        ],
        [
            "CATG19007",
            [MOUSE],
            "Home > Tecnología-Computadores > Accesorios gamer > Mouse gamer",
            1,
        ],
        [
            "cat202303",
            [VIDEO_GAME_CONSOLE],
            "Home > Tecnología-Videojuegos > Consolas",
            1,
        ],
        [
            "cat3114",
            [OVEN],
            "Home > Electrohogar-Electrodomésticos Cocina > Hornos Eléctricos",
            1,
        ],
        [
            "cat3151",
            [OVEN],
            "Home > Electrohogar-Electrodomésticos Cocina > Microondas",
            1,
        ],
        [
            "cat3136",
            [WASHING_MACHINE],
            "Home > Electrohogar-Línea blanca > Lavado",
            1,
        ],
        [
            "cat4060",
            [WASHING_MACHINE],
            "Home > Electrohogar-Línea blanca > Lavado > Lavadoras",
            1,
        ],
        [
            "cat1700002",
            [WASHING_MACHINE],
            "Home > Electrohogar-Línea blanca > Lavado > Lavadoras-Secadoras",
            1,
        ],
        [
            "cat4088",
            [WASHING_MACHINE],
            "Home > Electrohogar-Línea blanca > Lavado > Secadoras",
            1,
        ],
        [
            "cat4061",
            [DISH_WASHER],
            "Home > Electrohogar-Línea blanca > Lavado > Lavavajillas",
            1,
        ],
        [
            "cat3205",
            [REFRIGERATOR],
            "Home > Electrohogar-Línea Blanca > Refrigeración > Refrigeradores",
            1,
        ],
        [
            "cat4091",
            [REFRIGERATOR],
            "Home > Electrohogar-Línea Blanca > Refrigeración > Refrigeradores > Side by side",
            1,
        ],
        [
            "cat4074",
            [REFRIGERATOR],
            "Home > Electrohogar-Línea Blanca > Refrigeración > Refrigeradores > No Frost",
            1,
        ],
        [
            "CATG19019",
            [REFRIGERATOR],
            "Home > Electrohogar-Línea Blanca > Refrigeración > Refrigeradores > Top Freezer",
            1,
        ],
        [
            "CATG19020",
            [REFRIGERATOR],
            "Home > Electrohogar-Línea Blanca > Refrigeración > Refrigeradores > Bottom Freezer",
            1,
        ],
        [
            "cat4054",
            [OVEN],
            "Home > Electrohogar-Línea blanca > Cocina > Hornos Empotrables",
            1,
        ],
        [
            "cat2019",
            [AIR_CONDITIONER],
            "Home > Electrohogar-Climatización > Aire acondicionado",
            1,
        ],
        [
            "cat4850013",
            [NOTEBOOK],
            "Home > Especiales-Otras categorias > PC gamer",
            1,
        ],
        [
            "cat3025",
            [VACUUM_CLEANER],
            "Home > Electrohogar-Aspirado y Limpieza > Aspiradoras",
            1,
        ],
        [
            "cat70028",
            [CAMERA],
            "Home > Tecnología-Fotografía > Cámaras Compactas",
            1,
        ],
        [
            "cat70029",
            [CAMERA],
            "Home > Tecnología-Fotografía > Cámaras Semiprofesionales",
            1,
        ],
        ["cat1130010", [STEREO_SYSTEM], "Home > Tecnología-Audio > Tornamesas", 1],
        [
            "cat9900007",
            [SPACE_HEATER],
            "Home > Electrohogar-Calefacción > Calefacción > Estufas Parafina Láser",
            1,
        ],
        [
            "cat9910024",
            [SPACE_HEATER],
            "Home > Electrohogar-Calefacción > Calefacción > Estufas Gas",
            1,
        ],
        [
            "cat9910006",
            [SPACE_HEATER],
            "Home > Electrohogar-Calefacción > Calefacción > Estufas Eléctricas",
            1,
        ],
        [
            "cat9910027",
            [SPACE_HEATER],
            "Home > Electrohogar-Calefacción > Calefacción > Estufas Pellet y Leña",
            1,
        ],
        [
            "cat2013",
            [WATER_HEATER],
            "Home > Cocina y Baño-Baño > Calefont y Termos",
            1,
        ],
        [
            "cat70012",
            [STOVE],
            "Home > Electrohogar - Línea blanca > Cocina > Cocina a gas",
            1,
        ],
        [
            "cat4045",
            [STOVE],
            "Home > Electrohogar - Línea blanca > Cocina > Encimeras",
            1,
        ],
    ]

    @classmethod
    def categories(cls):
        cats = []
        for entry in cls.category_paths:
            for cat in entry[1]:
                if cat not in cats:
                    cats.append(cat)

        return cats

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = cls.category_paths
        session = requests.Session(impersonate="chrome120")
        fast_mode = extra_args and extra_args.get("fast_mode", False)
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = e[:4]

            if len(e) == 5:
                extra_params = e[4]
            else:
                extra_params = {}

            if category not in local_categories:
                continue

            for seller_data in cls.seller:
                if fast_mode and not seller_data["include_in_fast_mode"]:
                    continue
                category_product_urls = cls._get_product_urls(
                    session, category_id, extra_params, seller_data["id"]
                )

                if seller_data["section_prefix"]:
                    full_section_name = "{} > {}".format(
                        seller_data["section_prefix"], section_name
                    )
                else:
                    full_section_name = section_name

                for idx, url in enumerate(category_product_urls):
                    product_entries[url].append(
                        {
                            "category_weight": category_weight,
                            "section_name": full_section_name,
                            "value": idx + 1,
                        }
                    )

        if fast_mode:
            # Since the fast mode skips sections, remove the partial section data retrieved
            for url in product_entries.keys():
                product_entries[url] = []
        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = requests.Session(impersonate="chrome120")

        base_url = "https://www.falabella.com/falabella-cl/search?Ntt={}&page={}"

        discovered_urls = []
        page = 1
        while True:
            if page > 150:
                raise Exception("Page overflow " + keyword)

            search_url = base_url.format(urllib.parse.quote(keyword), page)
            res = session.get(search_url, timeout=30)

            if res.status_code == 500:
                break

            soup = BeautifulSoup(res.text, "html.parser")

            script = soup.find("script", {"id": "__NEXT_DATA__"})
            json_data = json.loads(script.text)

            if "results" not in json_data["props"]["pageProps"]:
                break

            for product_data in json_data["props"]["pageProps"]["results"]:
                product_url = product_data["url"]
                discovered_urls.append(product_url)

                if len(discovered_urls) == threshold:
                    return discovered_urls

            page += 1

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        extra_args = extra_args or {}
        session = requests.Session(impersonate="chrome120")

        for i in range(3):
            try:
                response = session.get(url, timeout=30)
            except RequestsError:
                return []
            except UnicodeDecodeError:
                return []

            if response.status_code in [404, 500]:
                return []

            if "notFound" in response.url:
                return []

            content = response.text.replace("&#10;", "")

            if "NEXT_DATA" in content:
                return cls._products_for_url(
                    url, content, session, category=category, extra_args=extra_args
                )
            else:
                return []

    @classmethod
    def _get_product_urls(cls, session, category_id, extra_params, seller_id):
        discovered_urls = []
        # For some reason the "categoryName" param activates the sponsored
        # results
        base_url = (
            "https://www.falabella.com/s/browse/v1/listing/cl?"
            "&categoryId={}&categoryName=foo&sortBy={}&page={}"
        )

        for key, value in extra_params.items():
            base_url += "&{}={}".format(key, urllib.parse.quote(value))

        base_url += "&zones={}".format(urllib.parse.quote(cls.zones))

        # The first sorting will be given preference for
        # section position information

        sortings = [
            "_score%2Cdesc",
            # "derived.price.search%2Casc",
            # "product.brandName%2Casc",
            # "product.attribute.newIconExpiryDate%2Cdesc",
            # "product.averageOverallRating%2Cdesc",
        ]

        for idx, sorting in enumerate(sortings):
            page = 1

            while True:
                if page > 210:
                    raise Exception("Page overflow: " + category_id)

                pag_url = base_url.format(category_id, sorting, page)

                if cls.store_and_subdomain:
                    pag_url += "&subdomain={}&store={}".format(
                        cls.store_and_subdomain, cls.store_and_subdomain
                    )

                if seller_id:
                    pag_url += "&f.derived.variant.sellerId={}".format(seller_id)

                print(pag_url)

                res = cls.retrieve_json_page(session, pag_url)

                if "results" not in res or not res["results"]:
                    if page == 1:
                        logging.warning("Empty category: {}".format(category_id))
                    break

                for result in res["results"]:
                    product_url = result["url"]
                    # Remove weird special characters
                    product_url = product_url.encode("ascii", "ignore").decode("ascii")

                    if "?" in product_url:
                        product_url = "{}/{}".format(
                            product_url.split("?")[0], result["skuId"]
                        )

                    if product_url not in discovered_urls:
                        discovered_urls.append(product_url)

                page += 1

        return discovered_urls

    @classmethod
    def retrieve_json_page(cls, session, url, retries=5):
        if "?" in url:
            separator = "&"
        else:
            separator = "?"

        modified_url = "{}{}v={}".format(url, separator, random.random())

        try:
            res = session.get(modified_url, timeout=30)
            return json.loads(res.content.decode("utf-8"))["data"]
        except Exception:
            if retries > 0:
                time.sleep(3)
                return cls.retrieve_json_page(session, url, retries=retries - 1)
            else:
                raise

    @classmethod
    def _products_for_url(cls, url, content, session, category=None, extra_args=None):
        soup = BeautifulSoup(content, "html.parser")
        next_container = soup.find("script", {"id": "__NEXT_DATA__"})

        if not next_container:
            return []

        product_data = json.loads(next_container.text)["props"]["pageProps"][
            "productData"
        ]

        specification_tag = soup.find("div", "productInfoContainer")
        long_description = product_data["longDescription"]

        if long_description:
            description_soup = BeautifulSoup(unescape(long_description), "html.parser")
        else:
            description_soup = None

        panels = [specification_tag, description_soup]
        video_urls = []
        description = ""

        for panel in panels:
            if not panel:
                continue

            description += html_to_markdown(str(panel))

            for iframe in panel.findAll("iframe"):
                if "src" not in iframe.attrs:
                    continue

                match = re.search(r"//www.youtube.com/embed/(.+)\?", iframe["src"])
                if not match:
                    match = re.search(r"//www.youtube.com/embed/(.+)", iframe["src"])
                if match:
                    video_url = "https://www.youtube.com/watch?v={}".format(
                        match.groups()[0].strip()
                    )
                    if validators.url(video_url):
                        video_urls.append(video_url)

        slug = product_data["slug"]
        publication_id = product_data["id"]
        brand = product_data["brandName"] or "Genérico"
        base_name = "{} {}".format(brand, product_data["name"])
        # Remove weird unicode characters
        base_name = base_name.encode("ascii", "ignore").decode("ascii")

        products = []

        if "variants" not in product_data:
            return []

        reviews_url = (
            "https://api.bazaarvoice.com/data/display/"
            "0.2alpha/product/summary?PassKey="
            "m8bzx1s49996pkz12xvk6gh2e&productid={}&"
            "contentType=reviews,questions&"
            "reviewDistribution=primaryRating,"
            "recommended&rev=0".format(product_data["id"])
        )

        review_data = json.loads(session.get(reviews_url, timeout=30).text)
        review_count = review_data["reviewSummary"]["numReviews"]
        review_avg_score = review_data["reviewSummary"]["primaryRating"]["average"]

        is_international_shipping = product_data["internationalShipping"]["applicable"]

        for model in product_data["variants"]:
            sku = model["id"]
            sku_url = (
                "https://www.falabella.com/falabella-cl/product/{}/{}/"
                "{}".format(publication_id, slug, sku)
            )

            prices = {e["type"]: e for e in model["prices"]}

            if not prices:
                continue

            normal_price_keys = ["eventPrice", "internetPrice", "normalPrice"]
            offer_price_keys = ["cmrPrice", "eventPrice"]

            normal_price = None
            offer_price = None

            for key in normal_price_keys:
                if key not in prices:
                    continue
                normal_price = Decimal(remove_words(prices[key]["price"][0]))
                if normal_price.is_finite():
                    break
                else:
                    normal_price = None

            for key in offer_price_keys:
                if key not in prices:
                    continue
                offer_price = Decimal(remove_words(prices[key]["price"][0]))
                if offer_price.is_finite():
                    break
                else:
                    offer_price = None

            if not normal_price and not offer_price:
                # No valid prices found
                continue

            if not offer_price:
                offer_price = normal_price

            if not normal_price:
                normal_price = offer_price

            if normal_price == Decimal("9999999") or offer_price == Decimal("9999999"):
                continue

            seller_entry = None

            if model["offerings"] and "sellerName" in model["offerings"][0]:
                if "falabella" not in model["offerings"][0]["sellerName"].lower():
                    seller_entry = model["offerings"][0]
            elif model["offerings"] and "sellerId" in model["offerings"][0]:
                if "falabella" not in model["offerings"][0]["sellerId"].lower():
                    seller_entry = model["offerings"][0]

            stock = 0

            if seller_entry:
                seller = (
                    seller_entry.get("sellerName", seller_entry["sellerId"]) or None
                )
                valid_sellers = [x["id"] for x in cls.seller]

                if seller not in valid_sellers:
                    stock = 0
                elif is_international_shipping:
                    stock = 0
                elif seller in cls.seller_blacklist:
                    stock = 0
                else:
                    if seller_entry.get(
                        "sellerProductStatus", None
                    ) == "ACTIVO" or seller_entry.get("isActive", False):
                        stock = -1
                    else:
                        stock = 0
            else:
                seller = None
                if not is_international_shipping and model.get("isPurchaseable", True):
                    availabilities = model["availability"]

                    for availability in availabilities:
                        if availability["shippingOptionType"] in [
                            "All",
                            "HomeDelivery",
                            "SiteToStore",
                            "PickupInStore",
                        ]:
                            if availability["quantity"]:
                                stock = -1
                                break
                    else:
                        stock = 0

            if "reacondicionado" in base_name.lower():
                condition = "https://schema.org/RefurbishedCondition"
            elif "reacondicionado" in description.lower():
                condition = "https://schema.org/RefurbishedCondition"
            else:
                condition = "https://schema.org/NewCondition"

            picture_urls = [
                x["url"] + "?scl=1.0"
                for x in model["medias"]
                if validators.url(x["url"])
            ]
            model_name = model["name"].encode("ascii", "ignore").decode("ascii")

            p = Product(
                "{} ({})".format(base_name, model_name)[:200],
                cls.__name__,
                category,
                sku_url,
                url,
                sku,
                stock,
                normal_price,
                offer_price,
                "CLP",
                sku=sku,
                picture_urls=picture_urls,
                video_urls=video_urls,
                review_count=review_count,
                review_avg_score=review_avg_score,
                condition=condition,
                seller=seller,
                description=description,
            )

            products.append(p)

        return products

    @classmethod
    def banners(cls, extra_args=None):
        banners = []

        for (
            section,
            subsection,
            subsection_type,
            url_suffix,
        ) in cls.banners_sections_data:
            url = cls.banners_base_url.format(url_suffix)
            print(url)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                session = requests.Session(impersonate="chrome120")
                soup = BeautifulSoup(session.get(url, timeout=30).text, "html.parser")
                next_data = json.loads(
                    soup.find("script", {"id": "__NEXT_DATA__"}).text
                )

                for container in next_data["props"]["pageProps"]["page"]["containers"]:
                    if container["key"] == "showcase":
                        showcase_container = container
                        break
                else:
                    raise Exception("No showcase container found")

                for container in showcase_container["components"]:
                    if "slides" in container["data"]:
                        slides = container["data"]["slides"]
                        break
                else:
                    raise Exception("No slides found")

                for idx, slide in enumerate(slides):
                    main_url = slide.get("mainUrl", None)
                    if main_url:
                        destination_urls = [main_url[:500]]
                    elif slide["type"] == "background_image_only":
                        destination_urls = []
                    else:
                        destination_urls = list({slide["urlLeft"], slide["urlRight"]})
                    picture_url = slide["imgBackgroundDesktopUrl"]

                    banners.append(
                        {
                            "url": url,
                            "picture_url": picture_url,
                            "destination_urls": destination_urls,
                            "key": picture_url,
                            "position": idx + 1,
                            "section": section,
                            "subsection": subsection,
                            "type": subsection_type,
                        }
                    )
            elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                session = requests.Session(impersonate="chrome120")
                soup = BeautifulSoup(session.get(url, timeout=30).text, "html.parser")
                next_data = json.loads(
                    soup.find("script", {"id": "__NEXT_DATA__"}).text
                )

                for container in next_data["props"]["pageProps"]["page"]["containers"]:
                    if container["key"] == "main-right":
                        showcase_container = container
                        break
                else:
                    raise Exception("No showcase container found")

                if not showcase_container["components"]:
                    continue

                slides = showcase_container["components"][0]["data"]["slides"]

                for idx, slide in enumerate(slides):
                    main_url = slide.get("mainUrl", None)
                    if main_url:
                        destination_urls = [main_url]
                    elif slide["type"] == "background_image_only":
                        destination_urls = []
                    else:
                        destination_urls = list({slide["urlLeft"], slide["urlRight"]})
                    picture_url = slide["imgBackgroundDesktopUrl"]

                    banners.append(
                        {
                            "url": url,
                            "picture_url": picture_url,
                            "destination_urls": destination_urls,
                            "key": picture_url,
                            "position": idx + 1,
                            "section": section,
                            "subsection": subsection,
                            "type": subsection_type,
                        }
                    )
            elif subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                session = requests.Session(impersonate="chrome120")
                soup = BeautifulSoup(session.get(url).text, "html.parser")
                banner = soup.find("div", "fb-huincha-main-wrap")

                if not banner:
                    print("No banner for " + url)
                    continue

                image_url = banner.find("source")["srcset"]
                dest_url = banner.find("a")["href"]

                banners.append(
                    {
                        "url": url,
                        "picture_url": image_url,
                        "destination_urls": [dest_url],
                        "key": image_url,
                        "position": 1,
                        "section": section,
                        "subsection": subsection,
                        "type": subsection_type,
                    }
                )

        return banners

    @classmethod
    def _get_picture_urls(cls, session, product_id):
        pictures_resource_url = (
            "https://falabella.scene7.com/is/image/"
            "Falabella/{}?req=set,json".format(product_id)
        )
        pictures_response = session.get(pictures_resource_url, timeout=30).text
        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);', pictures_response).groups()[0]
        )

        picture_urls = []

        picture_entries = pictures_json["set"]["item"]
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = (
                "https://falabella.scene7.com/is/image/{}?"
                "wid=1500&hei=1500&qlt=70".format(picture_entry["i"]["n"])
            )
            picture_urls.append(picture_url)

        return picture_urls

    @classmethod
    def reviews_for_sku(cls, sku):
        print(sku)
        session = session_with_proxy(None)
        reviews = []
        offset = 0

        while True:
            print(offset)
            endpoint = (
                "https://api.bazaarvoice.com/data/batch.json?"
                "passkey=m8bzx1s49996pkz12xvk6gh2e&apiversion="
                "5.5&resource.q0=reviews&filter.q0=isratings"
                "only%3Aeq%3Afalse&filter.q0=productid%3Aeq"
                "%3A{}&limit.q0=100&offset.q0={}".format(sku, offset)
            )
            response = session.get(endpoint).json()["BatchedResults"]["q0"]["Results"]

            if not response:
                break

            for entry in response:
                review_date = parse(entry["SubmissionTime"])

                review = {
                    "store": "Falabella",
                    "sku": sku,
                    "rating": float(entry["Rating"]),
                    "text": entry["ReviewText"],
                    "date": review_date.isoformat(),
                }

                reviews.append(review)

            offset += 100

        return reviews
