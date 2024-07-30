import json
import logging
import re
import urllib
from collections import defaultdict
from decimal import Decimal

import validators
from bs4 import BeautifulSoup
from dateutil.parser import parse

from storescraper.categories import (
    GAMING_CHAIR,
    TELEVISION,
    VACUUM_CLEANER,
    WATER_HEATER,
    STOVE,
    STEREO_SYSTEM,
    HEADPHONES,
    CELL,
    WEARABLE,
    TABLET,
    NOTEBOOK,
    VIDEO_GAME_CONSOLE,
    PRINTER,
    MONITOR,
    SOLID_STATE_DRIVE,
    PROJECTOR,
    MOUSE,
    KEYBOARD,
    COMPUTER_CASE,
    REFRIGERATOR,
    WASHING_MACHINE,
    DISH_WASHER,
    OVEN,
    SPACE_HEATER,
    AIR_CONDITIONER,
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
        ["tecnologia/computadores/tablets/", TABLET, 1],
        ["electro/audio/audifonos/", HEADPHONES, 1],
        ["electro/audio/parlantes-bluetooth-portables/", STEREO_SYSTEM, 1],
        ["electro/television/", TELEVISION, 1],
        ["electro/television/smart-tv/", TELEVISION, 1],
        ["electro/television/televisores-led/", TELEVISION, 1],
        ["television/televisores-oled-qled/", TELEVISION, 1],
        ["electro/television/soundbar-home-theater/", STEREO_SYSTEM, 1],
        ["electro/audio/", STEREO_SYSTEM, 0],
        ["electro/audio/micro-minicomponentes/", STEREO_SYSTEM, 1],
        ["electro/audio/audifonos-inalambricos/", HEADPHONES, 1],
        ["electro/audio-hifi/", STEREO_SYSTEM, 1],
        ["electro/audio-hifi/audifonos/", HEADPHONES, 1],
        ["electro/audio-hifi/home-theater/", STEREO_SYSTEM, 1],
        ["electro/audio-hifi/audio/", STEREO_SYSTEM, 1],
        ["electro/audio-hifi/parlantes/", STEREO_SYSTEM, 1],
        ["electro/elige-tu-pulgada/", TELEVISION, 1],
        ["electro/elige-tu-pulgada/30-a-39-pulgadas/", TELEVISION, 1],
        ["electro/elige-tu-pulgada/40-a-49-pulgadas/", TELEVISION, 1],
        ["electro/elige-tu-pulgada/50-a-59-pulgadas/", TELEVISION, 1],
        ["electro/elige-tu-pulgada/60-o-mas-pulgadas/", TELEVISION, 1],
        ["electro/elige-tu-pulgada/70-o-mas-pulgadas/", TELEVISION, 1],
        ["tecnologia/celulares/", CELL, 1],
        ["tecnologia/celulares/smartphone/", CELL, 1],
        ["tecnologia/celulares/iphone/", CELL, 1],
        ["tecnologia/celulares/samsung/", CELL, 1],
        ["tecnologia/celulares/xiaomi/", CELL, 1],
        ["tecnologia/celulares/motorola/", CELL, 1],
        ["tecnologia/celulares/honor/", CELL, 1],
        ["tecnologia/celulares/vivo/", CELL, 1],
        ["tecnologia/celulares/basicos/", CELL, 1],
        ["tecnologia/celulares/oppo/", CELL, 1],
        ["tecnologia/computadores/", NOTEBOOK, 0],
        ["tecnologia/computadores/notebooks/", NOTEBOOK, 1],
        ["tecnologia/computadores/ipad-tablet/", TABLET, 1],
        ["tecnologia/computadores/tablets-ninos/", TABLET, 1],
        ["tecnologia/computadores/apple/", NOTEBOOK, 1],
        ["tecnologia/wearables/", WEARABLE, 1],
        ["tecnologia/wearables/smartwatches/", WEARABLE, 1],
        ["tecnologia/wearables/smartwatches-ninos/", WEARABLE, 1],
        ["tecnologia/wearables/smartband/", WEARABLE, 1],
        ["tecnologia/consolas-videojuegos/", VIDEO_GAME_CONSOLE, 0],
        ["tecnologia/consolas-videojuegos/playstation2/", VIDEO_GAME_CONSOLE, 1],
        ["tecnologia/consolas-videojuegos/nintendo/", VIDEO_GAME_CONSOLE, 1],
        ["tecnologia/consolas-videojuegos/xbox/", VIDEO_GAME_CONSOLE, 1],
        ["tecnologia/consolas-videojuegos/consolas-nintendo/", VIDEO_GAME_CONSOLE, 1],
        [
            "tecnologia/consolas-videojuegos/consolas-playstation/",
            VIDEO_GAME_CONSOLE,
            1,
        ],
        ["tecnologia/consolas-videojuegos/consolas-xbox/", VIDEO_GAME_CONSOLE, 1],
        ["tecnologia/impresoras/", PRINTER, 1],
        ["tecnologia/impresoras/laser/", PRINTER, 1],
        ["tecnologia/impresoras/tinta/", PRINTER, 1],
        ["tecnologia/impresoras/termicas-portatiles/", PRINTER, 1],
        ["tecnologia/impresoras/impresoras-3d/", PRINTER, 1],
        ["tecnologia/impresoras/impresion-industrial/", PRINTER, 1],
        ["tecnologia/impresoras/rotuladores/", PRINTER, 1],
        ["tecnologia/accesorios-computacion/monitor-gamer/", MONITOR, 1],
        ["tecnologia/accesorios-computacion/disco-duro/", SOLID_STATE_DRIVE, 1],
        ["tecnologia/accesorios-computacion/proyectores/", PROJECTOR, 1],
        ["tecnologia/accesorios-computacion/mouse-teclados/", MOUSE, 1],
        ["tecnologia/accesorios-computacion/audifonos-microfonos/", HEADPHONES, 1],
        ["tecnologia/computadores/pc-gamer/", NOTEBOOK, 1],
        ["tecnologia/gamer/teclados/", KEYBOARD, 1],
        ["tecnologia/gamer/headset/", HEADPHONES, 1],
        ["tecnologia/gamer/sillas-escritorios-gamer/", GAMING_CHAIR, 1],
        ["tecnologia/gamer/gabinetes/", COMPUTER_CASE, 1],
        ["linea-blanca/refrigeracion/", REFRIGERATOR, 1],
        ["linea-blanca/refrigeracion/freezer/", REFRIGERATOR, 1],
        [
            "linea-blanca/refrigeracion/refrigeradores/refrigerador-side-by-side/",
            REFRIGERATOR,
            1,
        ],
        ["linea-blanca/refrigeracion/refrigeradores/", REFRIGERATOR, 1],
        ["linea-blanca/refrigeracion/refrigeradores/no-frost/", REFRIGERATOR, 1],
        ["linea-blanca/refrigeracion/frigobar-cavas/", REFRIGERATOR, 1],
        ["linea-blanca/equipamiento-industrial/refrigeracion/", REFRIGERATOR, 1],
        ["linea-blanca/lavado-secado/", WASHING_MACHINE, 1],
        [
            "linea-blanca/lavado-secado/todas/?prefn1=lavadoTipodeCarga&prefv1=Frontal",
            WASHING_MACHINE,
            1,
        ],
        [
            "linea-blanca/lavado-secado/todas/?prefn1=lavadoTipodeCarga&prefv1=Superior",
            WASHING_MACHINE,
            1,
        ],
        ["linea-blanca/lavado-secado/todas/", WASHING_MACHINE, 1],
        ["linea-blanca/lavado-secado/lavadoras-secadoras/", WASHING_MACHINE, 1],
        ["linea-blanca/lavado-secado/secadoras-centrifugas/", WASHING_MACHINE, 1],
        ["linea-blanca/lavado-secado/lavavajillas/", DISH_WASHER, 1],
        ["linea-blanca/cocina/", STOVE, 0],
        ["linea-blanca/cocina/cocinas/", STOVE, 1],
        ["linea-blanca/cocina/encimeras/", STOVE, 1],
        ["linea-blanca/cocina/hornos-empotrables/", OVEN, 1],
        ["linea-blanca/cocina/kit-empotrables/", STOVE, 1],
        ["linea-blanca/electrodomesticos/microondas/", OVEN, 1],
        ["linea-blanca/electrodomesticos/hornos-electricos/", OVEN, 1],
        ["linea-blanca/estufas/", SPACE_HEATER, 1],
        ["linea-blanca/estufas/electricas/", SPACE_HEATER, 1],
        ["linea-blanca/estufas/parafina/", SPACE_HEATER, 1],
        ["linea-blanca/estufas/gas/", SPACE_HEATER, 1],
        ["linea-blanca/estufas/lena-pellets/", SPACE_HEATER, 1],
        ["linea-blanca/estufas/calefaccion-exterior/", SPACE_HEATER, 1],
        ["linea-blanca/estufas/calefones-termos/", WATER_HEATER, 1],
        ["linea-blanca/electrodomesticos/aspiradoras-enceradoras/", VACUUM_CLEANER, 1],
        ["linea-blanca/aspirado-limpieza/aspiradoras-arrastre/", VACUUM_CLEANER, 1],
        ["linea-blanca/aspirado-limpieza/aspiradoras-robot/", VACUUM_CLEANER, 1],
        ["linea-blanca/aspirado-limpieza/aspiradoras-verticales/", VACUUM_CLEANER, 1],
        ["linea-blanca/climatizacion/", AIR_CONDITIONER, 1],
        [
            "linea-blanca/climatizacion/aires-acondicionado/aires-acondicionados-portatiles/",
            AIR_CONDITIONER,
            1,
        ],
        [
            "linea-blanca/climatizacion/aires-acondicionado/aires-acondicionados-split/",
            AIR_CONDITIONER,
            1,
        ],
        ["linea-blanca/climatizacion/aires-acondicionado/", AIR_CONDITIONER, 1],
        ["linea-blanca/climatizacion/ventilacion/", AIR_CONDITIONER, 1],
        ["linea-blanca/climatizacion/tratamiento-aire/", AIR_CONDITIONER, 1],
    ]

    @classmethod
    def categories(cls):
        cats = []
        for entry in cls.category_paths:
            cat = entry[1]
            if cat not in cats:
                cats.append(cat)

        return cats

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = cls.category_paths
        fast_mode = extra_args and extra_args.get("fast_mode", False)

        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = cls.USER_AGENT
        session.headers["apiKey"] = "cl-ccom-parisapp-plp"
        session.headers["platform"] = "web"

        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            (category_path, local_category, weight) = e

            if local_category != category:
                continue

            base_url = "https://www.paris.cl/" + category_path
            logging.info("Obtaining base section data from " + base_url)
            response = session.get(base_url)
            soup = BeautifulSoup(response.text, "lxml")
            category_id = re.search(
                r'dw\.ac\.applyContext\(\{category: "(.+)"', response.text
            ).groups()[0]
            breadcrumbs_tag = soup.find("div", "PLPbreadcrumbs")
            breadcrumbs = []
            for link_tag in breadcrumbs_tag.find_all("a", "breadcrumb-element"):
                breadcrumbs.append(link_tag.text.strip())
            breadcrumbs.append(
                breadcrumbs_tag.find("span", "breadcrumb-result-text").text.strip()
            )
            added_filters_breadcrumbs_tag = soup.find("div", "clear-refinement")
            if added_filters_breadcrumbs_tag:
                for added_filters_breadcrumb in added_filters_breadcrumbs_tag.findAll(
                    "span"
                ):
                    filter_breadcrumb = added_filters_breadcrumb.text.strip()
                    if filter_breadcrumb:
                        breadcrumbs.append(filter_breadcrumb)
            section_name = " > ".join(breadcrumbs)

            parsed_url = urllib.parse.urlparse(base_url)
            url_params = urllib.parse.parse_qs(parsed_url.query)

            filters = ["cgid=" + category_id]

            filter_idx = 1
            while True:
                label_name = "prefn" + str(filter_idx)
                if label_name in url_params:
                    filter_name = url_params[label_name][0]
                    filter_value = url_params["prefv" + str(filter_idx)][0]
                    filters.append("{}={}".format(filter_name, filter_value))
                else:
                    break
                filter_idx += 1

            if fast_mode:
                filters.append("isMarketplace=Paris")

            page = 0

            while True:
                if page > (15000 / cls.RESULTS_PER_PAGE):
                    raise Exception("Page overflow: " + category_id)

                filter_strings = []
                for idx, filter_str in enumerate(filters):
                    filter_strings.append("refine_{}={}".format(idx + 1, filter_str))
                filters_query = "&".join(filter_strings)

                endpoint = "https://cl-ccom-parisapp-plp.ecomm.cencosud.cl/v2/getServicePLP/0/{}/24?{}".format(
                    page * cls.RESULTS_PER_PAGE, filters_query
                )
                logging.info(endpoint)
                response = session.get(endpoint)

                json_response = response.json()
                containers_data = json_response["payload"]["data"]

                if "hits" not in containers_data:
                    break

                for idx, container in enumerate(containers_data["hits"]):
                    product_url = "https://www.paris.cl/product-{}.html".format(
                        container["product_id"]
                    )

                    product_entries[product_url].append(
                        {
                            "category_weight": weight,
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

            soup = BeautifulSoup(session.get(search_url).text, "lxml")
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

        soup = BeautifulSoup(response.text, "lxml")

        product_match = re.search(
            r"window.productJSON = ([\s\S]+)window.device", response.text
        )
        if not product_match:
            return []
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
            if "src" not in iframe.attrs:
                continue
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
            response.url,
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
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        )
        banners = []

        res = session.get("https://www.paris.cl/")
        soup = BeautifulSoup(res.text, "lxml")
        page_json = json.loads(soup.find("script", {"id": "__NEXT_DATA__"}).text)

        for idx, banner_entry in enumerate(
            page_json["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"][
                "data"
            ]["data"]["data"]["content"][0]["items"]
        ):
            picture_url = banner_entry["image"]

            banners.append(
                {
                    "url": "https://www.paris.cl/",
                    "picture_url": picture_url,
                    "destination_urls": [banner_entry["link"][:500]],
                    "key": picture_url,
                    "position": idx + 1,
                    "section": "Home",
                    "subsection": bs.SUBSECTION_TYPE_HOME,
                    "type": bs.HOME,
                }
            )
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
