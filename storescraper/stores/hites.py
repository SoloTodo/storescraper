import json
import logging
import re

from collections import defaultdict
from curl_cffi import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from storescraper.categories import (
    AIR_CONDITIONER,
    ALL_IN_ONE,
    CELL,
    DISH_WASHER,
    EXTERNAL_STORAGE_DRIVE,
    GAMING_CHAIR,
    HEADPHONES,
    KEYBOARD,
    MEMORY_CARD,
    MONITOR,
    MOUSE,
    NOTEBOOK,
    OVEN,
    PRINTER,
    PROJECTOR,
    REFRIGERATOR,
    SPACE_HEATER,
    STEREO_SYSTEM,
    STOVE,
    TABLET,
    TELEVISION,
    USB_FLASH_DRIVE,
    VIDEO_GAME_CONSOLE,
    WASHING_MACHINE,
    WEARABLE,
    WATER_HEATER,
)

from storescraper.flixmedia import flixmedia_video_urls
from storescraper.product import Product
from storescraper.store import Store
from storescraper import banner_sections as bs


class Hites(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TELEVISION,
            TABLET,
            REFRIGERATOR,
            PRINTER,
            OVEN,
            STOVE,
            WASHING_MACHINE,
            CELL,
            STEREO_SYSTEM,
            VIDEO_GAME_CONSOLE,
            ALL_IN_ONE,
            SPACE_HEATER,
            KEYBOARD,
            MOUSE,
            HEADPHONES,
            EXTERNAL_STORAGE_DRIVE,
            MONITOR,
            PROJECTOR,
            AIR_CONDITIONER,
            USB_FLASH_DRIVE,
            WEARABLE,
            DISH_WASHER,
            GAMING_CHAIR,
            WATER_HEATER,
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            [
                "electro-hogar/refrigeradores",
                [REFRIGERATOR],
                "Inicio > Electro Hogar > Refrigeradores",
                1,
            ],
            [
                "electro-hogar/refrigeradores/refrigerador-frio-directo",
                [REFRIGERATOR],
                "Inicio > Electro Hogar > Refrigeradores > Frío Directo",
                1,
            ],
            [
                "electro-hogar/refrigeradores/refrigerador-no-frost",
                [REFRIGERATOR],
                "Inicio > Electro Hogar > Refrigeradores > No Frost",
                1,
            ],
            [
                "electro-hogar/refrigeradores/refrigerador-side-by-side",
                [REFRIGERATOR],
                "Inicio > Electro Hogar > Refrigeradores > Side by Side",
                1,
            ],
            [
                "electro-hogar/refrigeradores/refrigerador-bottom-freezer",
                [REFRIGERATOR],
                "Inicio > Electro Hogar > Refrigeradores > Refrigerador "
                "Bottom Freezer",
                1,
            ],
            [
                "electro-hogar/refrigeradores/refrigerador-top-freezer",
                [REFRIGERATOR],
                "Inicio > Electro Hogar > Refrigeradores > Refrigerador " "Top Freezer",
                1,
            ],
            [
                "electro-hogar/refrigeradores/freezer-y-frigobar",
                [REFRIGERATOR],
                "Inicio > Electro Hogar > Refrigeradores > Freezers y Frigobar",
                1,
            ],
            [
                "electro-hogar/lavado-y-secado",
                [WASHING_MACHINE],
                "Inicio > Electro Hogar > Lavado y Secado",
                1,
            ],
            [
                "electro-hogar/lavado-y-secado/lavadoras",
                [WASHING_MACHINE],
                "Inicio > Electro Hogar > Lavado y Secado > Lavadoras",
                1,
            ],
            [
                "electro-hogar/lavado-y-secado/secadoras/",
                [WASHING_MACHINE],
                "Inicio > Electro Hogar > Lavado y Secado > Secadoras",
                1,
            ],
            [
                "electro-hogar/lavado-y-secado/lavadoras-secadoras",
                [WASHING_MACHINE],
                "Inicio > Electro Hogar > Lavado y Secado > Lavadoras-Secadoras",
                1,
            ],
            [
                "electro-hogar/lavado-y-secado/carga-frontal",
                [WASHING_MACHINE],
                "Inicio > Electro Hogar > Lavado y Secado > Carga Frontal",
                1,
            ],
            [
                "electro-hogar/lavado-y-secado/carga-superior",
                [WASHING_MACHINE],
                "Inicio > Electro Hogar > Lavado y Secado > Carga Superior",
                1,
            ],
            [
                "electro-hogar/cocina",
                [OVEN, STOVE],
                "Inicio > Electro Hogar > Cocina",
                0,
            ],
            [
                "electro-hogar/cocina/cocina-a-gas",
                [STOVE],
                "Inicio > Electro Hogar > Cocina > Cocina a gas",
                1,
            ],
            [
                "electro-hogar/lavado-y-secado/lavavajillas",
                [DISH_WASHER],
                "Inicio > Electro Hogar > Cocina > Lavavajillas",
                1,
            ],
            [
                "electro-hogar/cocina/encimeras",
                [STOVE],
                "Inicio > Electro Hogar > Cocina > Encimeras",
                1,
            ],
            [
                "electro-hogar/cocina/hornos-empotrados",
                [OVEN],
                "Inicio > Electro Hogar > Cocina > Hornos Empotrados",
                1,
            ],
            [
                "electro-hogar/electrodomesticos-cocina/microondas",
                [OVEN],
                "Inicio > Electro Hogar > Electrodomesticos Cocina > Microondas",
                1,
            ],
            [
                "electro-hogar/electrodomesticos-cocina/hornos-electricos",
                [OVEN],
                "Inicio > Electro Hogar > Electrodomesticos Cocina > "
                "Hornos Eléctricos",
                1,
            ],
            [
                "electro-hogar/calefaccion",
                [SPACE_HEATER],
                "Inicio > Electro Hogar > Calefacción",
                0,
            ],
            [
                "electro-hogar/calefaccion/estufas-a-gas",
                [SPACE_HEATER],
                "Inicio > Electro Hogar > Calefacción > Estufas a Gas",
                1,
            ],
            [
                "electro-hogar/calefaccion/f/estufa-a-lena",
                [SPACE_HEATER],
                "Inicio > Electro Hogar > Calefacción > Estufa a Leña",
                1,
            ],
            [
                "electro-hogar/calefaccion/estufas-electricas",
                [SPACE_HEATER],
                "Inicio > Electro Hogar > Calefacción > Estufas Eléctricas",
                1,
            ],
            [
                "electro-hogar/climatizacion",
                [AIR_CONDITIONER],
                "Inicio > Electro Hogar > Climatización",
                0,
            ],
            [
                "electro-hogar/climatizacion/f/aire-acondicionado",
                [AIR_CONDITIONER],
                "Inicio > Electro Hogar > Climatizacioń >  " "Aire Acondicionado",
                1,
            ],
            [
                "tecnologia/tv-video",
                [TELEVISION, STEREO_SYSTEM, PROJECTOR],
                "Inicio > Tecnología > TV Video",
                0,
            ],
            [
                "tecnologia/tv-video/smart-tv",
                [TELEVISION],
                "Inicio > Tecnología > Tv Video > Smart TV",
                1,
            ],
            [
                "tecnologia/tv-video/smart-tv-premium",
                [TELEVISION],
                "Inicio > Tecnología > Tv Video > Smart TV Premium",
                1,
            ],
            # ['tecnologia/tv-video/smart-tv-hasta-49', ['Television'],
            #  'Inicio > Tecnología > Tv Video > Smart TV Hasta 49', 1],
            # ['tecnologia/tv-video/smart-tv-entre-50-y-55', ['Television'],
            #  'Inicio > Tecnología > Tv Video > Smart TV Entre 50 y 55', 1],
            # ['tecnologia/tv-video/smart-tv-desde-58', ['Television'],
            #  'Inicio > Tecnología > Tv Video > Smart TV Desde 58', 1],
            [
                "tecnologia/tv-video/smart-tv-samsung",
                [TELEVISION],
                "Inicio > Tecnología > Tv Video > Smart Tv Samsung",
                1,
            ],
            [
                "tecnologia/tv-video/smart-tv-lg",
                [TELEVISION],
                "Inicio > Tecnología > Tv Video > Smart Tv LG",
                1,
            ],
            [
                "tecnologia/tv-video/smart-tv-hisense",
                [TELEVISION],
                "Inicio > Tecnología > Tv Video > Smart Tv Hisense",
                1,
            ],
            [
                "tecnologia/tv-video/f/soundbar",
                [STEREO_SYSTEM],
                "Inicio > Tecnología > TV Video > Soundbar",
                1,
            ],
            [
                "tecnologia/tv-video/proyectores",
                [PROJECTOR],
                "Inicio > Tecnología > TV Video > Proyectores",
                1,
            ],
            [
                "tecnologia/computacion",
                [NOTEBOOK, TABLET, PRINTER, MONITOR, ALL_IN_ONE],
                "Inicio > Tecnología > Computación",
                0,
            ],
            [
                "tecnologia/computacion/notebook",
                [NOTEBOOK],
                "Inicio > Tecnología > Computación > Notebook",
                1,
            ],
            [
                "tecnologia/computacion/tablets",
                [TABLET],
                "Inicio > Tecnología > Computación > Tablets",
                1,
            ],
            [
                "tecnologia/computacion/computadores-y-all-in-one",
                [ALL_IN_ONE],
                "Inicio > Tecnología > Computacioń > All in One",
                1,
            ],
            [
                "tecnologia/computacion/monitores",
                [MONITOR],
                "Inicio > Tecnología > Computación > Monitores y Proyectores",
                1,
            ],
            [
                "tecnologia/computacion/impresoras-y-multifuncionales",
                [PRINTER],
                "Inicio > Tecnología > Computación > " "Impresoras y Multifuncionales",
                1,
            ],
            [
                "tecnologia/videojuegos/consolas",
                [VIDEO_GAME_CONSOLE],
                "Inicio > Tecnología > Video Juego > Consolas",
                1,
            ],
            [
                "tecnologia/accesorios-y-otros/mouse-y-teclados",
                [MOUSE, KEYBOARD],
                "Inicio > Tecnología > Accesorios y Otros > Mouse y Teclados",
                0.5,
            ],
            [
                "tecnologia/accesorios-y-otros/pendrives-y-tarjetas-de-memoria",
                [USB_FLASH_DRIVE, MEMORY_CARD],
                "Inicio > Tecnología > Accesorios y Otros > Pendrives y "
                "Tarjetas de Memoria",
                1,
            ],
            [
                "tecnologia/accesorios-y-otros/discos-duros-y-pendrives",
                [EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE],
                "Inicio > Tecnología > Accesorios y Otros > Discos Duros"
                " y Pendrives",
                0.5,
            ],
            [
                "tecnologia/audio",
                [STEREO_SYSTEM, HEADPHONES],
                "Inicio > Tecnología > Audio",
                0,
            ],
            [
                "tecnologia/audio/parlantes-bluetooth",
                [STEREO_SYSTEM],
                "Inicio > Tecnología > Audio > Parlantes Bluetooth",
                1,
            ],
            [
                "tecnologia/audio/karaokes",
                [STEREO_SYSTEM],
                "Inicio > Tecnología > Audio > Karaokes",
                1,
            ],
            [
                "tecnologia/audio/minicomponentes",
                [STEREO_SYSTEM],
                "Inicio > Tecnología > Audio > Minicomponentes",
                1,
            ],
            [
                "celulares/audio/audifonos",
                [HEADPHONES],
                "Inicio > Celulares > Accesorios para celulares > Audífonos",
                1,
            ],
            [
                "celulares/audio/audifonos-inalambrico",
                [HEADPHONES],
                "Inicio > Celulares > Accesorios para celulares > Audífonos"
                " Inalámbrico",
                1,
            ],
            [
                "tecnologia/mundo-gamer/notebook-gamer",
                [NOTEBOOK],
                "Tecnología > Mundo Gamer > Notebook Gamer",
                1,
            ],
            [
                "tecnologia/mundo-gamer/monitores-gamer",
                [MONITOR],
                "Tecnología > Mundo Gamer > Monitores Gamer",
                1,
            ],
            [
                "tecnologia/mundo-gamer/sillas-gamer",
                [GAMING_CHAIR],
                "Tecnología > Mundo Gamer > Sillas Gamer",
                1,
            ],
            [
                "tecnologia/mundo-gamer/audifonos-gamer",
                [HEADPHONES],
                "Tecnología > Mundo Gamer > Audífonos Gamer",
                1,
            ],
            [
                "tecnologia/mundo-gamer/mouse-y-teclados-gamer",
                [MOUSE, KEYBOARD],
                "Tecnología > Mundo Gamer > Mouse y Teclados Gamer",
                0.5,
            ],
            ["celulares/smartphones", [CELL], "Inicio > Celulares > Smartphones", 1],
            [
                "celulares/smartphones/smartphone",
                [CELL],
                "Inicio > Celulares > Smartphones > Smartphones",
                1,
            ],
            [
                "celulares/smartphones/celulares-liberados",
                [CELL],
                "Inicio > Celulares > Smartphones > Celulares Liberados",
                1,
            ],
            [
                "celulares/smartphones/smartphones-reacondicionados",
                [CELL],
                "Inicio > Celulares > Smartphones > Celulares Reacondicionados",
                1,
            ],
            [
                "celulares/smartphones/celulares-basicos",
                [CELL],
                "Inicio > Celulares > Smartphone > Celulares Basicos",
                1,
            ],
            [
                "celulares/wearables/smartwatch",
                [WEARABLE],
                "Inicio > Celulares > Accesorios para celulares > Smartwatch",
                1,
            ],
            [
                "celulares/accesorios-para-celulares/audifonos",
                [HEADPHONES],
                "Inicio > Celulares > Accesorios para celulares > Audífonos",
                1,
            ],
            [
                "electro-hogar/calefaccion/calefont-y-termos",
                [WATER_HEATER],
                "Inicio > Electro Hogar > Calefacción > Calefont y Termos",
                1,
            ],
        ]

        product_entries = defaultdict(lambda: [])
        session = requests.Session(impersonate="chrome120")

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            start = 0
            current_position = 1
            step = 48

            while True:
                category_url = (
                    "https://www.hites.com/{}/?sz={}&start={}&"
                    "srule=best-matches".format(category_path, step, start)
                )
                print(category_url)

                if start >= step * 100:
                    raise Exception("Page overflow: " + category_url)

                response = session.get(category_url, timeout=60)
                if response.url != category_url:
                    raise Exception(
                        "Page mismatch. Expecting {} Got {}"
                        "".format(category_url, response.url)
                    )

                if response.status_code in [404, 500]:
                    break

                soup = BeautifulSoup(response.text, "lxml")

                products = soup.findAll("div", "product-tile")

                if not products:
                    # if start == 0:
                    #     raise Exception(category_url)
                    break

                for product_entry in products:
                    path = product_entry.find("a")["href"].split("?")[0]

                    if "hites.com" in path:
                        product_url = path
                    else:
                        product_url = "https://www.hites.com" + path

                    if product_url == "https://www.hites.com/":
                        logging.warning("Invalid URL: " + category_url)
                        continue

                    product_entries[product_url].append(
                        {
                            "category_weight": category_weight,
                            "section_name": section_name,
                            "value": current_position,
                        }
                    )
                    current_position += 1

                start += step

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = requests.Session(impersonate="chrome120")
        product_urls = []

        page = 1

        while True:
            if page > 40:
                raise Exception("Page overflow")

            search_url = "https://www.hites.com/search/{}?page={}".format(keyword, page)
            print(search_url)

            response = session.get(search_url, timeout=60)

            if response.status_code in [404, 500]:
                return []

            soup = BeautifulSoup(response.text, "lxml")
            json_data = json.loads(soup.find("script", {"id": "hy-data"}).text)
            product_data = json_data["result"]["products"]

            if not product_data:
                break

            for product_entry in product_data:
                slug = product_entry["productString"]
                product_url = "https://www.hites.com/" + slug
                product_urls.append(product_url)
                if len(product_urls) == threshold:
                    return product_urls

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = requests.Session(impersonate="chrome120")
        response = session.get(url, timeout=60)

        if response.status_code in [404, 410]:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, "lxml")

        if soup.find("section", "error-page"):
            return []

        if soup.find("img", {"src": "/public/statics/images/404.svg"}):
            return []

        name = soup.find("h1", "product-name").text
        sku = soup.find("span", "product-id").text

        prices = soup.find("div", "prices")

        offer_price_container = prices.find("span", "hites-price")
        offer_price = None
        if offer_price_container:
            offer_price = Decimal(
                offer_price_container.text.split("$")[1].replace(".", "").strip()
            )

        normal_price_container = prices.find("span", "sales")
        if not normal_price_container:
            normal_price_container = prices.find("span", "list")

        if not normal_price_container and not offer_price_container:
            return []

        normal_price = Decimal(normal_price_container.find("span", "value")["content"])

        if not offer_price:
            offer_price = normal_price

        has_virtual_assistant = "cdn.livechatinc.com/tracking.js" in response.text

        flixmedia_container = soup.find(
            "script", {"src": "//media.flixfacts.com/js/loader.js"}
        )
        flixmedia_id = None
        video_urls = None

        if flixmedia_container:
            mpn = flixmedia_container["data-flix-mpn"]
            video_urls = flixmedia_video_urls(mpn)
            if video_urls is not None:
                flixmedia_id = mpn

        if "reacondicionado" in name.lower():
            condition = "https://schema.org/RefurbishedCondition"
        else:
            condition = "https://schema.org/NewCondition"

        images = soup.find("div", "primary-images").findAll("div", "carousel-item")

        picture_urls = [
            i.find("img")["src"].replace(" ", "%20")
            for i in images
            if i.find("img") is not None
        ]

        seller = soup.find("b", "seller").text.strip()

        if seller == "Hites":
            seller = None

        availability_match = re.search(r'"availability":"(.+)"}', response.text)
        availability_text = availability_match.groups()[0]

        if seller:
            stock = 0
        elif availability_text == "http://schema.org/OutOfStock":
            stock = 0
        elif availability_text == "http://schema.org/InStock":
            stock = -1
        else:
            raise Exception("Invalid availability text: {}".format(availability_text))

        review_count_tag = soup.find("span", "top-stars-rating-details")

        if review_count_tag:
            review_count = int(review_count_tag.text.replace("(", "").replace(")", ""))
        else:
            review_count = 0

        if review_count:
            review_score_tag = soup.find("div", "yotpo-score-average")
            review_avg_score = float(review_score_tag.find("span").text)
        else:
            review_avg_score = None

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
            condition=condition,
            picture_urls=picture_urls,
            video_urls=video_urls,
            has_virtual_assistant=has_virtual_assistant,
            flixmedia_id=flixmedia_id,
            seller=seller,
            review_count=review_count,
            review_avg_score=review_avg_score,
        )

        return [p]

    @classmethod
    def banners(cls, extra_args=None):
        base_url = "https://www.hites.com/{}"

        sections_data = [
            # [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            [
                bs.TELEVISIONS,
                "TV Video",
                bs.SUBSECTION_TYPE_MOSAIC,
                "tecnologia/tv-video",
            ],
            [
                bs.TELEVISIONS,
                "Smart TV LG",
                bs.SUBSECTION_TYPE_MOSAIC,
                "tecnologia/tv-video/smart-tv-lg",
            ],
            [
                bs.TELEVISIONS,
                "Smart TV Samsung",
                bs.SUBSECTION_TYPE_MOSAIC,
                "tecnologia/tv-video/smart-tv-samsung",
            ],
            [
                bs.TELEVISIONS,
                "Smart TV Hisense",
                bs.SUBSECTION_TYPE_MOSAIC,
                "tecnologia/tv-video/smart-tv-hisense",
            ],
            [
                bs.TELEVISIONS,
                "Smart TV Premium",
                bs.SUBSECTION_TYPE_MOSAIC,
                "tecnologia/tv-video/smart-tv-premium",
            ],
            [
                bs.CELLS,
                "Smartphone",
                bs.SUBSECTION_TYPE_MOSAIC,
                "celulares/smartphones",
            ],
            [
                bs.CELLS,
                "Smartphone-Smartphone",
                bs.SUBSECTION_TYPE_MOSAIC,
                "celulares/smartphones/smartphone",
            ],
            [
                bs.CELLS,
                "Smartphone Liberados",
                bs.SUBSECTION_TYPE_MOSAIC,
                "celulares/smartphones/celulares-liberados",
            ],
            [
                bs.REFRIGERATION,
                "Refrigeradores",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro-hogar/refrigeradores",
            ],
            [
                bs.REFRIGERATION,
                "No Frost",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro-hogar/refrigeradores/refrigerador-no-frost",
            ],
            [
                bs.REFRIGERATION,
                "Side by Side",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro-hogar/refrigeradores/refrigerador-side-by-side",
            ],
            [
                bs.WASHING_MACHINES,
                "Lavado y Secado",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro-hogar/lavado-y-secado",
            ],
            [
                bs.WASHING_MACHINES,
                "Lavadoras",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro-hogar/lavado-y-secado/lavadoras",
            ],
            [
                bs.WASHING_MACHINES,
                "Lavadoras-Secadoras",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro-hogar/lavado-y-secado/lavadoras-secadoras",
            ],
            # [bs.WASHING_MACHINES, 'Secadoras', bs.SUBSECTION_TYPE_MOSAIC,
            #  'electro-hogar/lavado-y-secado/secadoras'],
            [bs.AUDIO, "Audio", bs.SUBSECTION_TYPE_MOSAIC, "tecnologia/audio"],
            # [bs.AUDIO, 'Minicomponentes', bs.SUBSECTION_TYPE_MOSAIC,
            #  'tecnologia/audio/minicomponentes'],
            # [bs.AUDIO, 'Soundbar y Home Theater', bs.SUBSECTION_TYPE_MOSAIC,
            #  'tecnologia/audio/soundbar-y-home-theater']
        ]

        session = requests.Session(impersonate="chrome120")
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            print(url)

            if subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                response = session.get(url)
                soup = BeautifulSoup(response.text, "lxml")

                banners_container = soup.find("section").findAll(
                    "div", "espot", recursive=False
                )

                for index, banner in enumerate(banners_container):
                    destination_urls = [d["href"] for d in banner.findAll("a")]

                    destination_urls = list(set(destination_urls))

                    picture_container = banner.find("picture")
                    picture_source = picture_container.find("source")

                    if not picture_source:
                        continue

                    picture_url = picture_source["srcset"]
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
        return banners
