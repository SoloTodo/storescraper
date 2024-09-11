import logging
from collections import defaultdict

import validators
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    TELEVISION,
    STEREO_SYSTEM,
    HEADPHONES,
    SPACE_HEATER,
    REFRIGERATOR,
    WASHING_MACHINE,
    DISH_WASHER,
    VACUUM_CLEANER,
    OVEN,
    CELL,
    WEARABLE,
    NOTEBOOK,
    TABLET,
    MOUSE,
    GAMING_CHAIR,
    EXTERNAL_STORAGE_DRIVE,
    PRINTER,
    VIDEO_GAME_CONSOLE,
    WATER_HEATER,
    STOVE,
    AIR_CONDITIONER,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper import banner_sections as bs


class AbcDin(Store):
    base_url = "https://www.abcdin.cl"
    site_name = "Abcdin"

    ajax_resources = [
        ["celulares", [CELL], "Tecnología / Celulares", 0.5],
        ["smartphones", [CELL], "Tecnología / Celulares / Smartphones", 1],
        ["smartwatch", [WEARABLE], "Tecnología / Celulares / Smartwatch", 1],
        [
            "accesorios-telefonos",
            [HEADPHONES],
            "Tecnología / Celulares / Accesorios Teléfonos",
            1,
        ],
        [
            "ver-todo-celulares",
            [CELL],
            "Tecnología / Celulares / Ver todo Celulares",
            1,
        ],
        [
            "televisores",
            [TELEVISION],
            "Tecnología / Televisores",
            1,
        ],
        [
            "smart-tv",
            [TELEVISION],
            "Tecnología / Televisores / Smart TV",
            1,
        ],
        [
            "soundbar",
            [STEREO_SYSTEM],
            "Tecnología / Televisores / Soundbar",
            1,
        ],
        [
            "ver-todo-televisores",
            [TELEVISION, STEREO_SYSTEM],
            "Tecnología / Televisores / Ver todo Televisores",
            0.5,
        ],
        [
            "computadores",
            [NOTEBOOK, TABLET, PRINTER],
            "Tecnología / Computadores",
            0.5,
        ],
        [
            "notebooks",
            [NOTEBOOK],
            "Tecnología / Computadores / Notebooks",
            1,
        ],
        [
            "tablet",
            [TABLET],
            "Tecnología / Computadores / Tablet",
            1,
        ],
        [
            "todo-impresoras",
            [PRINTER],
            "Tecnología / Computadores / Impresoras",
            1,
        ],
        [
            "ver-todo-computadores",
            [NOTEBOOK, TABLET, PRINTER],
            "Tecnología / Computadores / Todo Computadores",
            0.5,
        ],
        [
            "audio",
            [STEREO_SYSTEM, HEADPHONES],
            "Tecnología / Audio",
            0.5,
        ],
        [
            "minicomponentes",
            [STEREO_SYSTEM],
            "Tecnología / Audio / Minicomponentes",
            1,
        ],
        [
            "parlantes-portátiles",
            [STEREO_SYSTEM],
            "Tecnología / Audio / Parlantes portátiles",
            1,
        ],
        [
            "audifonos",
            [HEADPHONES],
            "Tecnología / Audio / Audífonos",
            1,
        ],
        [
            "soundbar",
            [STEREO_SYSTEM],
            "Tecnología / Audio / Soundbar",
            1,
        ],
        [
            "ver-todo-audio",
            [STEREO_SYSTEM, HEADPHONES],
            "Tecnología / Audio / Ver todo Audio",
            0.5,
        ],
        [
            "discos-duros",
            [EXTERNAL_STORAGE_DRIVE],
            "Tecnología / Accesorios Computación / Discos Duros",
            1,
        ],
        [
            "mouse-i-teclados",
            [MOUSE],
            "Tecnología / Accesorios Computación / Mouse y Teclados",
            1,
        ],
        [
            "notebooks-gamer",
            [NOTEBOOK],
            "Tecnología / Mundo Gamer / Notebooks Gamer",
            1,
        ],
        [
            "consolas",
            [VIDEO_GAME_CONSOLE],
            "Tecnología / Mundo Gamer / Consolas",
            1,
        ],
        [
            "audifonos-gamer",
            [HEADPHONES],
            "Tecnología / Mundo Gamer / Audífonos Gamer",
            1,
        ],
        [
            "sillas-gamer",
            [GAMING_CHAIR],
            "Tecnología / Mundo Gamer / Sillas Gamer",
            1,
        ],
        [
            "accesorios-gamer",
            [MOUSE],
            "Tecnología / Mundo Gamer / Accesorios Gamer",
            1,
        ],
        [
            "refrigeradores",
            [REFRIGERATOR],
            "Línea Blanca / Refrigeradores",
            1,
        ],
        [
            "freezer",
            [REFRIGERATOR],
            "Línea Blanca / Refrigeradores / Freezer",
            1,
        ],
        [
            "side-by-side",
            [REFRIGERATOR],
            "Línea Blanca / Refrigeradores / Side by Side",
            1,
        ],
        [
            "no-frost",
            [REFRIGERATOR],
            "Línea Blanca / Refrigeradores / No Frost",
            1,
        ],
        [
            "frio-directo",
            [REFRIGERATOR],
            "Línea Blanca / Refrigeradores / Frío Directo",
            1,
        ],
        [
            "frigobar",
            [REFRIGERATOR],
            "Línea Blanca / Refrigeradores / Frigobar",
            1,
        ],
        [
            "ver-todo-refrigeracion",
            [REFRIGERATOR],
            "Línea Blanca / Refrigeradores / Ver todo Refrigeración",
            1,
        ],
        [
            "lavado-y-secado",
            [WASHING_MACHINE],
            "Línea Blanca / Lavado y Secado",
            1,
        ],
        [
            "lavadoras",
            [WASHING_MACHINE],
            "Línea Blanca / Lavado y Secado / Lavadoras",
            1,
        ],
        [
            "secadoras",
            [WASHING_MACHINE],
            "Línea Blanca / Lavado y Secado / Secadoras",
            1,
        ],
        [
            "lavadoras-secadoras",
            [WASHING_MACHINE],
            "Línea Blanca / Lavado y Secado / Lavadoras - Secadoras",
            1,
        ],
        [
            "ver-todo-lavado-y-secado",
            [WASHING_MACHINE],
            "Línea Blanca / Lavado y Secado / Ver todo Lavado y Secado",
            1,
        ],
        [
            "hornos-electricos",
            [OVEN],
            "Línea Blanca / Electrodomésticos / Hornos Eléctricos",
            1,
        ],
        [
            "microondas",
            [OVEN],
            "Línea Blanca / Electrodomésticos / Microondas",
            1,
        ],
        [
            "cocinas-a-gas",
            [STOVE],
            "Línea Blanca / Cocina / Cocinas a Gas",
            1,
        ],
        [
            "encimeras",
            [STOVE],
            "Línea Blanca / Cocina / Encimeras",
            1,
        ],
        [
            "hornos-empotrables",
            [OVEN],
            "Línea Blanca / Cocina / Hornos empotrables",
            1,
        ],
        [
            "lavaplatos-y-lavavajillas",
            [DISH_WASHER],
            "Línea Blanca / Cocina / Lavaplatos y Lavavajillas",
            1,
        ],
        [
            "aires-acondicionados",
            [AIR_CONDITIONER],
            "Línea Blanca / Climatización / Aires Acondicionados",
            1,
        ],
        [
            "calefont-y-termos",
            [WATER_HEATER],
            "Línea Blanca / Climatización / Calefont y Termos",
            1,
        ],
        [
            "estufas",
            [SPACE_HEATER],
            "Línea Blanca / Climatización / Estufas",
            1,
        ],
        [
            "aspiradoras",
            [VACUUM_CLEANER],
            "Línea Blanca / Aseo y Limpieza / Aspiradoras",
            1,
        ],
        [
            "aspiradoras-robot",
            [VACUUM_CLEANER],
            "Línea Blanca / Aseo y Limpieza / Aspiradoras Robot",
            1,
        ],
    ]

    @classmethod
    def categories(cls):
        cats = list()
        for category_id, local_categories, section, weight in cls.ajax_resources:
            for local_category in local_categories:
                if local_category not in cats:
                    cats.append(local_category)
        return cats

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        discovered_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )

        for (
            category_id,
            local_categories,
            section_name,
            category_weight,
        ) in cls.ajax_resources:
            if category not in local_categories:
                continue

            url = (
                "{}/on/demandware.store/Sites-{}-Site/es_CL/Search-UpdateGrid?cgid={}&"
                "srule=best-matches&sz=1000"
            ).format(cls.base_url, cls.site_name, category_id)
            print(url)

            res = session.get(url)
            soup = BeautifulSoup(res.text, "lxml")
            product_cells = soup.findAll("div", "product-tile__item")

            if not product_cells:
                logging.warning("Empty category: " + category_id)

            for idx, product_cell in enumerate(product_cells):
                product_path = product_cell.find("a", "image-link")

                if not product_path:
                    continue

                product_url = cls.base_url + product_path["href"]
                discovered_entries[product_url].append(
                    {
                        "category_weight": category_weight,
                        "section_name": section_name,
                        "value": idx + 1,
                    }
                )

        return discovered_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        url = (
            "{}/on/demandware.store/"
            "Sites-{}-Site/es_CL/Search-UpdateGrid?"
            "q={}&srule=product-outstanding"
            "&start=0&sz=1000".format(cls.base_url, cls.site_name, keyword)
        )

        response = session.get(url).text
        soup = BeautifulSoup(response, "lxml")

        products = soup.findAll("div", "lp-product-tile")

        if not products:
            return []

        for container in products:
            product_url = "{}{}".format(
                cls.base_url, container.find("a", "image-link")["href"]
            )
            product_urls.append(product_url)

            if len(product_urls) == threshold:
                return product_urls

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 410:
            return []

        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", {"itemprop": "name"}).text.strip()
        key = soup.find("span", {"itemprop": "sku"})["data-sku"]
        prices_tag = soup.find("div", "prices")
        internet_price_tag = prices_tag.find("p", "internet")

        if internet_price_tag:
            normal_price_tag = internet_price_tag.find("span", "price-value")
        else:
            js_internet_price_tag = prices_tag.find("p", "js-internet-price")

            if not js_internet_price_tag:
                return []

            normal_price_tag = js_internet_price_tag.find("span", "price-value")

        normal_price = Decimal(normal_price_tag["data-value"]).quantize(0)

        offer_price_tag = prices_tag.find("p", "js-tlp-price")

        if offer_price_tag:
            offer_price_text = offer_price_tag.find("span", "price-value")
            offer_price = Decimal(offer_price_text["data-value"]).quantize(0)
        else:
            offer_price = normal_price

        stock = -1
        sku_tag = soup.find("span", "cod")

        if sku_tag:
            sku = soup.find("span", "cod").text.split(":")[1].strip()
        else:
            sku = key

        description = html_to_markdown(str(soup.find("div", "description-and-detail")))
        picture_urls = [
            x.find("img")["src"]
            for x in soup.findAll("div", "primary-image")
            if validators.url(x.find("img")["src"])
        ]

        product = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            "CLP",
            sku=sku,
            description=description,
            picture_urls=picture_urls,
            # video_urls=video_urls,
            # flixmedia_id=flixmedia_id,
            # has_virtual_assistant=has_virtual_assistant
        )

        return [product]

    @classmethod
    def banners(cls, extra_args=None):
        session = session_with_proxy(extra_args)
        banners = []

        soup = BeautifulSoup(session.get(cls.base_url).text, "lxml")
        slider_tags = soup.findAll("div", "rojoPolar")

        for index, slider_tag in enumerate(slider_tags):
            destination_urls = [slider_tag.find("a")["href"]]
            picture_url = slider_tag.find("source")["srcset"]

            banners.append(
                {
                    "url": cls.base_url,
                    "picture_url": picture_url,
                    "destination_urls": destination_urls,
                    "key": picture_url,
                    "position": index + 1,
                    "section": bs.HOME,
                    "subsection": bs.HOME,
                    "type": bs.SUBSECTION_TYPE_HOME,
                }
            )
        return banners
