import json
import logging
import re
from collections import defaultdict
from decimal import Decimal

import validators
from bs4 import BeautifulSoup
from dateutil.parser import parse

from storescraper.categories import (
    GAMING_CHAIR,
    GAMING_DESK,
    TELEVISION,
    VACUUM_CLEANER,
    WATER_HEATER,
    STOVE,
)
from storescraper.flixmedia import flixmedia_video_urls
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy, remove_words
from storescraper import banner_sections as bs


class Paris(Store):
    USER_AGENT = "solotodobot"
    RESULTS_PER_PAGE = 24

    category_paths = [
        ["electro/television", ["Television"], "Electro > Televisión", 1],
        [
            "electro/television/smart-tv",
            ["Television"],
            "Electro > Televisión > Smart TV",
            1,
        ],
        [
            "electro/television/televisores-led",
            ["Television"],
            "Electro > Televisión > Televisores LED",
            1,
        ],
        [
            "television/televisores-oled-qled",
            ["Television"],
            "Electro > Televisión > Oled y Qled",
            1,
        ],
        [
            "electro/television/soundbar-home-theater",
            ["StereoSystem"],
            "Electro > Televisión > Soundbar y Home Theater",
            1,
        ],
        ["electro/elige-tu-pulgada", [TELEVISION], "Electro > Elige tu pulgada", 1],
        # Also contains other audio products
        ["electro/audio", ["StereoSystem", "Headphones"], "Electro > Audio", 0],
        [
            "electro/audio/parlantes-bluetooth-portables",
            ["StereoSystem"],
            "Electro > Audio > Parlantes Bluetooth y Portables",
            1,
        ],
        [
            "electro/audio/micro-minicomponentes",
            ["StereoSystem"],
            "Electro > Audio > Micro y Minicomponentes",
            1,
        ],
        ["electro/audio/audifonos", ["Headphones"], "Electro > Audio > Audífonos", 1],
        [
            "electro/audio/audifonos-inalambricos",
            ["Headphones"],
            "Electro > Audio > Audífonos Inalámbricos",
            1,
        ],
        # Also contains other audio products
        ["electro/audio-hifi", ["Headphones", "StereoSystem"], "Electro > HiFi", 0],
        [
            "electro/audio-hifi/audifonos",
            ["Headphones"],
            "Electro > HiFi > Audifonos HiFi",
            1,
        ],
        # ['electro/audio-hifi/home-theater', ['StereoSystem'],
        #  'Electro > HiFi > Home Cinema', 1],
        [
            "electro/audio-hifi/audio",
            ["StereoSystem"],
            "Electro > HiFi > Audio HiFi",
            1,
        ],
        [
            "electro/audio-hifi/parlantes",
            ["StereoSystem"],
            "Electro > HiFi > Parlantes HIFI",
            1,
        ],
        ["electro/audio-hifi", ["StereoSystem"], "Electro > HiFi > Combos HIFI", 1],
        [
            "tecnologia/computadores",
            ["Notebook", "Tablet", "AllInOne"],
            "Tecno > Computadores",
            0.5,
        ],
        [
            "tecnologia/computadores/notebooks",
            ["Notebook"],
            "Tecno > Computadores > Notebooks",
            1,
        ],
        [
            "tecnologia/computadores/pc-gamer",
            ["Notebook"],
            "Tecno > Computadores > PC Gamers",
            1,
        ],
        [
            "tecnologia/computadores/desktop-all-in-one",
            ["AllInOne"],
            "Tecno > Computadores > Desktop y All InOne",
            1,
        ],
        [
            "tecnologia/computadores/ipad-tablet",
            ["Tablet"],
            "Tecno > Computadores > iPad y Tablet",
            1,
        ],
        # Also includes accesories
        # ['tecnologia/celulares', ['Cell', 'Wearables'],
        #  'Tecno > Celulares', 0],
        [
            "tecnologia/celulares/smartphones",
            ["Cell"],
            "Tecno > Celulares > Smartphones",
            1,
        ],
        ["tecnologia/celulares/basicos", ["Cell"], "Tecno > Celulares > Básicos", 1],
        [
            "tecnologia/wearables/smartwatches",
            ["Wearable"],
            "Tecno > Wearables > Smartwatches",
            1,
        ],
        [
            "tecnologia/wearables/smartband",
            ["Wearable"],
            "Tecno > Wearables > Smartband",
            1,
        ],
        [
            "tecnologia/gamers",
            ["Notebook", "VideoGameConsole", "Keyboard", "Headphones"],
            "Tecno > Gamers",
            0.5,
        ],
        [
            "tecnologia/gamer/teclados",
            ["Keyboard"],
            "Tecno > Gamers > Teclados y Mouse",
            1,
        ],
        ["tecnologia/gamer/headset", ["Headphones"], "Tecno > Gamers > Headset", 1],
        # Also includes videogames
        [
            "tecnologia/consolas-videojuegos",
            ["VideoGameConsole"],
            "Tecno > Consolas VideoJuegos",
            0,
        ],
        [
            "tecnologia/consolas-videojuegos/playstation1",
            ["VideoGameConsole"],
            "Tecno > Consolas VideoJuegos > Consolas PlayStation",
            1,
        ],
        [
            "tecnologia/consolas-videojuegos/nintendo",
            ["VideoGameConsole"],
            "Tecno > Consolas VideoJuegos > Consolas Nintendo",
            1,
        ],
        [
            "tecnologia/impresoras/laser",
            ["Printer"],
            "Tecno > Impresoras > Impresión Láser",
            1,
        ],
        [
            "tecnologia/impresoras/tinta",
            ["Printer"],
            "Tecno > Impresoras > Impresión de Tinta",
            1,
        ],
        # Also includes other accesories
        [
            "tecnologia/accesorios-fotografia",
            ["MemoryCard"],
            "Tecno > Accesorios Fotografía",
            0,
        ],
        [
            "tecnologia/accesorios-fotografia/tarjetas-memoria",
            ["MemoryCard"],
            "Tecno > Accesorios Fotografía > Tarjetas de Memoria",
            1,
        ],
        # Also includes other accesories
        [
            "tecnologia/accesorios-computacion/monitor-gamer",
            ["Monitor"],
            "Tecno > Accesorios Computación > Monitores Gamer",
            1,
        ],
        [
            "tecnologia/accesorios-computacion/disco-duro",
            ["ExternalStorageDrive"],
            "Tecno > Accesorios Computación > Discos Duros",
            1,
        ],
        [
            "tecnologia/accesorios-computacion/proyectores",
            ["Projector"],
            "Tecno > Accesorios Computación > Proyectores",
            1,
        ],
        [
            "tecnologia/accesorios-computacion/mouse-teclados",
            ["Mouse"],
            "Tecno > Accesorios Computación > Mouse y Teclados",
            1,
        ],
        [
            "tecnologia/accesorios-computacion/pendrives",
            ["UsbFlashDrive"],
            "Tecno > Accesorios Computación > Pendrives",
            1,
        ],
        [
            "linea-blanca/refrigeracion",
            ["Refrigerator"],
            "Línea Blanca > Refrigeración",
            1,
        ],
        [
            "linea-blanca/refrigeracion/refrigeradores",
            ["Refrigerator"],
            "Línea Blanca > Refrigeración > Refrigeradores",
            1,
        ],
        [
            "linea-blanca/refrigeracion/refrigeradores/no-frost",
            ["Refrigerator"],
            "Línea Blanca > Refrigeración > No Frost",
            1,
        ],
        [
            "linea-blanca/refrigeracion/refrigeradores/" "refrigerador-top-mount",
            ["Refrigerator"],
            "Línea Blanca > Refrigeración > Top Mount",
            1,
        ],
        [
            "linea-blanca/refrigeracion/refrigeradores/" "refrigerador-bottom-freezer",
            ["Refrigerator"],
            "Línea Blanca > Refrigeración > Bottom Freezer",
            1,
        ],
        [
            "linea-blanca/refrigeracion/refrigeradores/refrigerador-side-by-side2",
            ["Refrigerator"],
            "Línea Blanca > Refrigeración > Side by Side",
            1,
        ],
        # ['linea-blanca/refrigeracion/frio-directo', ['Refrigerator'],
        #  'Línea Blanca > Refrigeración > Frío Directo', 1],
        # ['linea-blanca/refrigeracion/freezer', ['Refrigerator'],
        #  'Línea Blanca > Refrigeración > Freezer', 1],
        [
            "linea-blanca/refrigeracion/frigobar-cavas",
            ["Refrigerator"],
            "Línea Blanca > Refrigeración > Frigobares y Cavas",
            1,
        ],
        [
            "linea-blanca/lavado-secado",
            ["WashingMachine", "DishWasher"],
            "Línea Blanca > Lavado y Secado",
            0.5,
        ],
        [
            "linea-blanca/lavado-secado/todas",
            ["WashingMachine"],
            "Línea Blanca > Lavado y Secado > Todas las Lavadoras",
            1,
        ],
        [
            "linea-blanca/lavado-secado/lavadoras-secadoras",
            ["WashingMachine"],
            "Línea Blanca > Lavado y Secado > Lavadora-Secadoras",
            1,
        ],
        [
            "linea-blanca/lavado-secado/secadoras-centrifugas",
            ["WashingMachine"],
            "Línea Blanca > Lavado y Secado > Secadoras y Centrifugas",
            1,
        ],
        [
            "linea-blanca/lavado-secado/todas/?prefn1=lavadoTipodeCarga&prefv1=Frontal",
            ["WashingMachine"],
            "Línea Blanca > Lavado y Secado > Todas las Lavadoras Frontales",
            1,
        ],
        [
            "linea-blanca/lavado-secado/todas/?prefn1=lavadoTipodeCarga&prefv1=Superior",
            ["WashingMachine"],
            "Línea Blanca > Lavado y Secado > Todas las Lavadoras Superior",
            1,
        ],
        [
            "linea-blanca/lavado-secado/lavavajillas",
            ["DishWasher"],
            "Línea Blanca > Lavado y Secado > Lavavajillas",
            1,
        ],
        # Also includes campanas
        ["linea-blanca/cocina", ["Oven"], "Línea Blanca > Cocinas", 0],
        [
            "linea-blanca/cocina/encimeras",
            ["Oven"],
            "Línea Blanca > Cocinas > Encimeras",
            1,
        ],
        [
            "linea-blanca/cocina/hornos-empotrables",
            ["Oven"],
            "Línea Blanca > Cocinas > Hornos y Microondas empotrables",
            1,
        ],
        # Also includes other electrodomésticos
        [
            "linea-blanca/electrodomesticos",
            ["Oven"],
            "Línea Blanca > Electrodomésticos",
            0,
        ],
        [
            "linea-blanca/electrodomesticos/microondas",
            ["Oven"],
            "Línea Blanca > Electrodomésticos > Microondas",
            1,
        ],
        # Also includes ventiladores
        [
            "linea-blanca/climatizacion",
            ["SpaceHeater", "AirConditioner"],
            "Línea Blanca > Climatización",
            0,
        ],
        [
            "linea-blanca/climatizacion/aires-acondicionado",
            ["AirConditioner"],
            "Línea Blanca > Climatización > Aire Acondicionado",
            1,
        ],
        ["linea-blanca/estufas", ["SpaceHeater"], "Línea Blanca > Estufas", 1],
        [
            "linea-blanca/estufas/electricas",
            ["SpaceHeater"],
            "Línea Blanca > Estufas > Estufas Eléctricas",
            1,
        ],
        [
            "linea-blanca/electrodomesticos/aspiradoras-enceradoras",
            [VACUUM_CLEANER],
            "Línea Blanca > Electrodomésticos > Aspiradoras y Enceradoras",
            1,
        ],
        [
            "electro/television/accesorios-televisores",
            ["CellAccesory"],
            "Electro > Televisión > Accesorios para TV",
            1,
        ],
        [
            "muebles/oficina/sillas/sillas-gamer",
            [GAMING_CHAIR],
            "Muebles > Oficina > Sillas de Escritorio",
            1,
        ],
        [
            "tecnologia/gamers/escritorios-gamer",
            [GAMING_DESK],
            "Tecno > Gamer > Escritorios Gamer",
            1,
        ],
        [
            "linea-blanca/estufas/calefones-termos",
            [WATER_HEATER],
            "Electro y Línea Blanca > Calefacción > Calefont y Termos",
            1,
        ],
        [
            "linea-blanca/cocina/cocinas",
            [STOVE],
            "Electro y Línea Blanca > Cocina > Cocinas",
            1,
        ],
        [
            "linea-blanca/cocina/encimeras",
            [STOVE],
            "Electro y Línea Blanca > Cocina > Encimeras",
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
        fast_mode = extra_args and extra_args.get("fast_mode", False)

        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = cls.USER_AGENT
        product_entries = defaultdict(lambda: [])

        if fast_mode:
            seller_filter = "prefn1=isMarketplace&prefv1=Paris&"
        else:
            seller_filter = ""

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 0

            while True:
                if page > (15000 / cls.RESULTS_PER_PAGE):
                    raise Exception("Page overflow: " + category_path)

                if "?" in category_path:
                    separator = "&"
                else:
                    separator = "/?"

                category_url = "https://www.paris.cl/{}{}{}sz={}&start={}" "".format(
                    category_path,
                    separator,
                    seller_filter,
                    cls.RESULTS_PER_PAGE,
                    page * cls.RESULTS_PER_PAGE,
                )
                print(category_url)
                response = session.get(category_url)

                if response.url != category_url:
                    raise Exception(
                        "Mismatching URL: {} - {}".format(response.url, category_url)
                    )

                soup = BeautifulSoup(response.text, "html.parser")
                containers = soup.find("ul", {"id": "search-result-items"})

                if not containers:
                    break

                containers = containers.findAll("li", recursive=False)

                if not containers:
                    if page == 0:
                        logging.warning("Empty category: " + category_url)
                    break

                for idx, container in enumerate(containers):
                    product_link = container.find("a")
                    if not product_link:
                        continue
                    product_url = product_link["href"].split("?")[0]

                    if product_url.startswith("/"):
                        product_url = "https://www.paris.cl" + product_url

                    if product_url == "null":
                        continue

                    if product_url == "javascript:void(0);":
                        continue

                    if "https" not in product_url:
                        product_url = "https://www.paris.cl" + product_url

                    product_entries[product_url].append(
                        {
                            "category_weight": category_weight,
                            "section_name": section_name,
                            "value": cls.RESULTS_PER_PAGE * page + idx + 1,
                        }
                    )

                page += 1

        if fast_mode:
            # Since the fast mode filters the results, it messes up the position data, so remove it altogether
            for url in product_entries.keys():
                product_entries[url] = []
        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = cls.USER_AGENT
        product_urls = []

        page = 0

        while True:
            if page > 40:
                raise Exception("Page overflow")

            search_url = "https://www.paris.cl/search?q={}&sz={}&start={}".format(
                keyword, cls.RESULTS_PER_PAGE, page * cls.RESULTS_PER_PAGE
            )

            soup = BeautifulSoup(session.get(search_url).text, "html.parser")
            containers = soup.findAll("li", "flex-item-products")

            if not containers:
                break

            for container in containers:
                product_url = container.find("a")["href"].split("?")[0]
                if "https" not in product_url:
                    product_url = "https://www.paris.cl" + product_url

                product_urls.append(product_url)

                if len(product_urls) == threshold:
                    return product_urls

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = cls.USER_AGENT
        response = session.get(url)

        if response.status_code in [410, 404]:
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        product_match = re.search(
            r"window.productJSON = ([\s\S]+)window.device", response.text
        )
        product_data = json.loads(product_match.groups()[0])

        brand = product_data.get("brand", "Unknown")
        name = "{} - {}".format(brand, product_data["name"])
        sku = product_data["id"]

        normal_price = None
        offer_price = None
        list_price = None

        for price_entry in product_data["prices"]:
            if price_entry["priceBookId"] == "clp-internet-prices":
                normal_price = Decimal(remove_words(price_entry["price"]))
            elif price_entry["priceBookId"] == "clp-cencosud-prices":
                offer_price = Decimal(remove_words(price_entry["price"]))
            elif price_entry["priceBookId"] == "clp-list-prices":
                list_price = Decimal(remove_words(price_entry["price"]))

        if normal_price is None:
            normal_price = list_price

        if normal_price is None:
            return []

        if offer_price is None or offer_price > normal_price:
            offer_price = normal_price

        if normal_price > Decimal("100000000") or offer_price > Decimal("100000000"):
            return []

        image_groups = product_data["image_groups"]
        if image_groups:
            picture_urls = [
                x["link"]
                for x in image_groups[0]["images"]
                if validators.url(x["link"])
            ]
        else:
            picture_urls = None

        raw_seller = product_data["seller"]

        if raw_seller == "Paris.cl":
            seller = None
        else:
            seller = raw_seller

        if seller:
            stock = 0
        elif product_data["orderable"]:
            stock = -1
        else:
            stock = 0

        video_urls = []
        for iframe in soup.findAll("iframe"):
            match = re.match("https://www.youtube.com/embed/(.+)", iframe["src"])
            if match:
                video_urls.append(
                    "https://www.youtube.com/watch?v={}".format(match.groups()[0])
                )

        flixmedia_id = None

        flixmedia_tag = soup.find(
            "script", {"src": "//media.flixfacts.com/js/loader.js"}
        )
        if flixmedia_tag:
            mpn = flixmedia_tag["data-flix-mpn"].strip()
            flix_videos = flixmedia_video_urls(mpn)
            if flix_videos is not None:
                video_urls.extend(flix_videos)
                flixmedia_id = mpn

        description = html_to_markdown(str(soup.find("ul", "pdp-product-info")))

        reviews_endpoint = (
            "https://api.bazaarvoice.com/data/display/"
            "0.2alpha/product/summary?PassKey=cawhDUNXMzzke7y"
            "V6JTnIiPm8Eh0hP8s7Oqzo57qihXkk&productid="
            "{}&contentType=reviews&rev=0".format(sku)
        )
        review_data = json.loads(session.get(reviews_endpoint).text)
        review_count = review_data["reviewSummary"]["numReviews"]
        review_avg_score = review_data["reviewSummary"]["primaryRating"]["average"]

        conditions_dict = {
            "REACONDICIONADO": "https://schema.org/RefurbishedCondition",
            "SEGUNDA MANO": "https://schema.org/UsedCondition",
        }

        condition = "https://schema.org/NewCondition"
        for promotion in product_data["promotions"]:
            for label in promotion["labels"]:
                for condition_text, condition_cadidate in conditions_dict.items():
                    if condition_text in label.upper():
                        condition = condition_cadidate

        if "REACONDICIONADO" in name.upper():
            condition = "https://schema.org/RefurbishedCondition"

        has_virtual_assistant = brand == "LG"

        p = Product(
            name[:200],
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
            description=description,
            picture_urls=picture_urls,
            video_urls=video_urls,
            flixmedia_id=flixmedia_id,
            review_count=review_count,
            review_avg_score=review_avg_score,
            seller=seller,
            has_virtual_assistant=has_virtual_assistant,
            condition=condition,
        )

        return [p]

    @classmethod
    def banners(cls, extra_args=None):
        base_url = "https://www.paris.cl/{}"

        sections_data = [
            [bs.HOME, "Home", bs.SUBSECTION_TYPE_HOME, ""],
            # [bs.LINEA_BLANCA_PARIS, 'Línea Blanca Paris',
            #  bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'linea-blanca/'],
            # [bs.ELECTRO_PARIS, 'Electro Paris',
            #  bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'electro/'],
            [
                bs.TECNO_PARIS,
                "Tecno Paris",
                bs.SUBSECTION_TYPE_CATEGORY_PAGE,
                "tecnologia/",
            ],
            [
                bs.REFRIGERATION,
                "Refrigeración",
                bs.SUBSECTION_TYPE_MOSAIC,
                "linea-blanca/refrigeracion/",
            ],
            [
                bs.REFRIGERATION,
                "No Frost",
                bs.SUBSECTION_TYPE_MOSAIC,
                "linea-blanca/refrigeracion/no-frost/",
            ],
            [
                bs.REFRIGERATION,
                "Side by Side",
                bs.SUBSECTION_TYPE_MOSAIC,
                "linea-blanca/refrigeracion/refrigeradores/"
                "refrigerador-side-by-side/",
            ],
            [
                bs.WASHING_MACHINES,
                "Lavado y Secado",
                bs.SUBSECTION_TYPE_MOSAIC,
                "linea-blanca/lavado-secado/",
            ],
            [
                bs.WASHING_MACHINES,
                "Todas las Lavadoras",
                bs.SUBSECTION_TYPE_MOSAIC,
                "linea-blanca/lavado-secado/todas/",
            ],
            [
                bs.WASHING_MACHINES,
                "Lavadora-Secadoras",
                bs.SUBSECTION_TYPE_MOSAIC,
                "linea-blanca/lavado-secado/lavadoras-secadoras/",
            ],
            [
                bs.WASHING_MACHINES,
                "Secadoras y Centrifugas",
                bs.SUBSECTION_TYPE_MOSAIC,
                "linea-blanca/lavado-secado/secadoras-centrifugas/",
            ],
            [
                bs.TELEVISIONS,
                "Televisión",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro/television/",
            ],
            [
                bs.TELEVISIONS,
                "Todas las TV",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro/television/todas/",
            ],
            [
                bs.TELEVISIONS,
                "Smart TV",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro/television/smart-tv/",
            ],
            [
                bs.TELEVISIONS,
                "Televisores LED",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro/television/televisores-led/",
            ],
            [
                bs.TELEVISIONS,
                "Oled y Qled",
                bs.SUBSECTION_TYPE_MOSAIC,
                "television/televisores-oled-qled/",
            ],
            [
                bs.TELEVISIONS,
                "Monitor TV",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro/television/monitores-tv/",
            ],
            [bs.AUDIO, "Audio", bs.SUBSECTION_TYPE_MOSAIC, "electro/audio/"],
            [
                bs.AUDIO,
                "Parlantes Bluetooth y Portables",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro/audio/parlantes-bluetooth-portables/",
            ],
            [
                bs.AUDIO,
                " Micro y Minicomponentes",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro/audio/micro-minicomponentes/",
            ],
            [bs.CELLS, "Celulares", bs.SUBSECTION_TYPE_MOSAIC, "tecnologia/celulares/"],
            [
                bs.CELLS,
                "Smartphones",
                bs.SUBSECTION_TYPE_MOSAIC,
                "tecnologia/celulares/smartphones/",
            ],
        ]

        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            response = session.get(url)
            print(url)
            soup = BeautifulSoup(response.text, "html.parser")

            if subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                image = soup.find("section", "ocultar_banner_mobile")

                if not image:
                    image = soup.find("section", "ocultar_banner_plp_mobile")

                if not image:
                    continue

                if image.find("a"):
                    destination_urls = [image.find("a")["href"]]
                else:
                    destination_urls = []

                picture = image.find("picture")

                if not picture:
                    continue

                if picture.find("source"):
                    picture_url = picture.find("source")["srcset"]
                else:
                    picture_url = picture.find("img")["src"]

                banners.append(
                    {
                        "url": url,
                        "picture_url": picture_url,
                        "destination_urls": destination_urls,
                        "key": picture_url,
                        "position": 1,
                        "section": section,
                        "subsection": subsection,
                        "type": subsection_type,
                    }
                )
            elif subsection_type == bs.SUBSECTION_TYPE_HOME:
                res = session.get("https://www.paris.cl/")
                soup = BeautifulSoup(res.text, "html.parser")
                tags = soup.find("div", {"id": "__next"}).find("section").findAll("a")

                for idx, tag in enumerate(tags):
                    picture_url = tag.find("source")["srcset"]

                    banners.append(
                        {
                            "url": url,
                            "picture_url": picture_url,
                            "destination_urls": [tag["href"]],
                            "key": picture_url,
                            "position": idx + 1,
                            "section": section,
                            "subsection": subsection,
                            "type": subsection_type,
                        }
                    )
            elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                image_container = soup.find("div", "home-slider")

                if not image_container:
                    image_container = soup.find("div", "hero-slider")
                if not image_container:
                    image_container = soup.find("div", "slick-slider")
                if not image_container:
                    image_container = soup.find("div", "slider-magazine")
                if not image_container:
                    image_container = soup.find("section", "horizontal-scrollable")

                images = image_container.findAll("a")
                images = [i for i in images if i.find("picture")]

                assert len(images) > 0

                for index, image in enumerate(images):
                    picture_url = image.find("picture").find("source")["srcset"]
                    destination_url = image.get("href")
                    if destination_url:
                        destination_urls = [destination_url]

                        if len(destination_url) > 255:
                            continue
                    else:
                        destination_urls = []

                    banners.append(
                        {
                            "url": url,
                            "picture_url": picture_url,
                            "destination_urls": destination_urls,
                            "key": picture_url,
                            "position": index + 1,
                            "section": section,
                            "subsection": subsection,
                            "type": subsection_type,
                        }
                    )
            else:
                raise Exception("Invalid subsection type " "{}".format(subsection_type))

        return banners

    @classmethod
    def reviews_for_sku(cls, sku):
        print(sku)
        session = session_with_proxy(None)
        reviews = []

        reviews_endpoint = (
            "https://api.bazaarvoice.com/data/batch.json?pass"
            "key=caKNy0lDYfGnjpRhD27b7ZtxiSbxdwBcuuIEwXCyc9Zr"
            "M&apiversion=5.5&resource.q0=reviews&filter.q0=p"
            "roductid%3Aeq%3A{}&limit.q0=100".format(sku)
        )
        review_data = json.loads(session.get(reviews_endpoint).text)

        for entry in review_data["BatchedResults"]["q0"]["Results"]:
            review_date = parse(entry["SubmissionTime"])

            review = {
                "store": "Paris",
                "sku": sku,
                "rating": float(entry["Rating"]),
                "text": entry["ReviewText"],
                "date": review_date.isoformat(),
            }

            reviews.append(review)

        return reviews
