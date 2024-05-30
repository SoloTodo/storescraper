import json

import time

import xml.etree.ElementTree as ET
from collections import OrderedDict
from decimal import Decimal

import validators

from storescraper.categories import (
    AIR_CONDITIONER,
    ALL_IN_ONE,
    CELL,
    DISH_WASHER,
    GAMING_CHAIR,
    MEMORY_CARD,
    MONITOR,
    NOTEBOOK,
    MOUSE,
    HEADPHONES,
    OVEN,
    PRINTER,
    REFRIGERATOR,
    SOLID_STATE_DRIVE,
    SPACE_HEATER,
    STEREO_SYSTEM,
    TABLET,
    TELEVISION,
    USB_FLASH_DRIVE,
    VACUUM_CLEANER,
    VIDEO_GAME_CONSOLE,
    WASHING_MACHINE,
    WEARABLE,
    WATER_HEATER,
    STORAGE_DRIVE,
    STOVE,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy, check_ean13
from storescraper import banner_sections as bs


class LiderFeed(Store):
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.3"
    )
    category_paths = [
        ("Celulares > Audífonos y Accesorios > Audífonos", HEADPHONES),
        ("Celulares > Mundo Apple > AirPods", HEADPHONES),
        ("Celulares > Mundo Apple > Apple Watch", WEARABLE),
        ("Celulares > Mundo Apple > iPad", TABLET),
        ("Celulares > Mundo Apple > iPhone", CELL),
        ("Celulares > Mundo Apple > Mac", NOTEBOOK),
        ("Celulares > Relojes Inteligentes > Smartband", WEARABLE),
        ("Celulares > Relojes inteligentes > Smartwatch", WEARABLE),
        ("Celulares > Relojes inteligentes > Smartwatch Infantiles", WEARABLE),
        ("Celulares > Telefonía > Celulares Básicos", CELL),
        ("Celulares > Telefonía > Celulares reacondicionados", CELL),
        ("Celulares > Telefonía > Smartphone", CELL),
        ("Climatización > Calefacción > Calefactores", SPACE_HEATER),
        ("Climatización > Calefacción > Estufas a Gas", SPACE_HEATER),
        ("Climatización > Calefacción > Estufas a Leña y Pellet", SPACE_HEATER),
        ("Climatización > Calefacción > Estufas Eléctrica", SPACE_HEATER),
        ("Climatización > Calefacción > Termos y Calefonts", WATER_HEATER),
        ("Climatización > Ventilación > Aire Acondicionado", AIR_CONDITIONER),
        ("Computación > Accesorios Computación > Audífonos y Micrófonos", HEADPHONES),
        ("Computación > Accesorios Computación > Monitores y Proyectores", MONITOR),
        ("Computación > Accesorios Computación > Mouse y Teclados", MOUSE),
        ("Computación > Almacenamiento > Discos Duros", STORAGE_DRIVE),
        ("Computación > Almacenamiento > Discos Duros SSD", SOLID_STATE_DRIVE),
        ("Computación > Almacenamiento > Pendrives", USB_FLASH_DRIVE),
        ("Computación > Almacenamiento > Tarjetas de Memoria", MEMORY_CARD),
        ("Computación > Computadores > Computadores All in One", ALL_IN_ONE),
        ("Computación > Computadores > Notebooks", NOTEBOOK),
        ("Computación > Computadores > Tablets", TABLET),
        ("Computación > Impresión > Impresoras Láser", PRINTER),
        ("Computación > Impresión > Impresoras y Multifuncionales", PRINTER),
        ("Computación > Mundo Gamer > Audífonos", HEADPHONES),
        ("Computación > Mundo Gamer > Computación Gamer", NOTEBOOK),
        ("Computación > Mundo Gamer > Consolas", VIDEO_GAME_CONSOLE),
        ("Computación > Mundo Gamer > Mouse y Teclados", MOUSE),
        ("Computación > Mundo Gamer > Sillas Gamer", GAMING_CHAIR),
        (
            "Electrohogar > Aspirado y Limpieza > Aspiradoras de Arrastre y Ciclonica",
            VACUUM_CLEANER,
        ),
        (
            "Electrohogar > Aspirado y Limpieza > Aspiradoras Robot",
            VACUUM_CLEANER,
        ),
        (
            "Electrohogar > Aspirado y Limpieza > Aspiradoras Tambor",
            VACUUM_CLEANER,
        ),
        (
            "Electrohogar > Aspirado y Limpieza > Aspiradoras Verticales y Portatiles",
            VACUUM_CLEANER,
        ),
        (
            "Electrohogar > Climatización > Calefacción",
            SPACE_HEATER,
        ),
        (
            "Electrohogar > Climatización > Termos y Calefonts",
            WATER_HEATER,
        ),
        (
            "Electrohogar > Cocinas > Cocina a Gas",
            STOVE,
        ),
        (
            "Electrohogar > Cocinas > Encimeras",
            STOVE,
        ),
        (
            "Electrohogar > Cocinas > Hornos Empotrables",
            OVEN,
        ),
        (
            "Electrohogar > Electrodomésticos Cocina > Hornos Eléctricos",
            OVEN,
        ),
        (
            "Electrohogar > Electrodomésticos Cocina > Microondas",
            OVEN,
        ),
        (
            "Electrohogar > Lavado y Planchado > Lavadoras",
            WASHING_MACHINE,
        ),
        (
            "Electrohogar > Lavado Y Planchado > Lavadoras Secadoras",
            WASHING_MACHINE,
        ),
        (
            "Electrohogar > Lavado y Planchado > Lavavajillas",
            DISH_WASHER,
        ),
        (
            "Electrohogar > Lavado y Planchado > Secadoras",
            WASHING_MACHINE,
        ),
        (
            "Electrohogar > Refrigeración > Cavas",
            REFRIGERATOR,
        ),
        (
            "Electrohogar > Refrigeración > Freezer",
            REFRIGERATOR,
        ),
        (
            "Electrohogar > Refrigeración > Frigobar",
            REFRIGERATOR,
        ),
        (
            "Electrohogar > Refrigeración > Frío Directo",
            REFRIGERATOR,
        ),
        (
            "Electrohogar > Refrigeración > No Frost",
            REFRIGERATOR,
        ),
        (
            "Electrohogar > Refrigeración > Side by Side",
            REFRIGERATOR,
        ),
        (
            "Tecno > Audio > Audífonos",
            HEADPHONES,
        ),
        (
            "Tecno > Audio > Audio Portable",
            STEREO_SYSTEM,
        ),
        (
            "Tecno > Audio > Equipos de Música y Karaoke",
            STEREO_SYSTEM,
        ),
        (
            "Tecno > Audio > Micro y Mini Componentes",
            STEREO_SYSTEM,
        ),
        (
            "Tecno > Audio > Soundbars y Home Theater",
            STEREO_SYSTEM,
        ),
        (
            "Tecno > Mundo Gamer > Audífonos",
            HEADPHONES,
        ),
        (
            "Tecno > Mundo Gamer > Consolas",
            VIDEO_GAME_CONSOLE,
        ),
        (
            "Tecno > Mundo Gamer > Mouse y Teclados",
            MOUSE,
        ),
        (
            "Tecno > TV > Home Theater",
            STEREO_SYSTEM,
        ),
        (
            "Tecno > TV > Smart Tv",
            TELEVISION,
        ),
        (
            "Tecno > TV > Smart TV",
            TELEVISION,
        ),
        (
            "Tecno > TV > Smart TV Hasta 50 Pulgadas",
            TELEVISION,
        ),
        (
            "Tecno > TV > Smart TV Sobre 50 Pulgadas",
            TELEVISION,
        ),
        (
            "Tecno > Videojuegos > Consolas",
            VIDEO_GAME_CONSOLE,
        ),
    ]

    @classmethod
    def products(
        cls,
        categories=None,
        extra_args=None,
        discover_urls_concurrency=None,
        products_for_url_concurrency=None,
        use_async=None,
    ):
        sanitized_parameters = cls.sanitize_parameters(
            categories=categories,
            discover_urls_concurrency=discover_urls_concurrency,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async,
        )

        categories = sanitized_parameters["categories"]
        local_category_paths = {}
        for category_path, category in cls.category_paths:
            if category in categories:
                local_category_paths[category_path] = category
        print(local_category_paths)

        feed_url = "https://files.channable.com/fObMWIb605WbIhKBmwptpA==.xml"
        session = session_with_proxy(extra_args)
        res = session.get(feed_url)
        root = ET.fromstring(res.text)
        products = []
        for node in root:
            if node.find("custom_label_0").text == "MKP":
                # Ignore marketplace
                continue
            node_section = node.find("product_type").text
            if node_section not in local_category_paths:
                continue
            name = node.find("title").text
            category = local_category_paths[node_section]
            url = node.find("link").text
            key = node.find("id").text
            stock = -1
            normal_price = Decimal(node.find("sale_price").text)
            offer_price_text = node.find("price_lider").text
            if offer_price_text:
                offer_price = Decimal(offer_price_text)
            else:
                offer_price = normal_price
            picture_urls = [node.find("image_link").text]
            description = node.find("description").text

            p = Product(
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
                sku=key,
                picture_urls=picture_urls,
                description=description,
            )
            products.append(p)

        return {"products": products, "discovery_urls_without_products": []}

    @classmethod
    def categories(cls):
        cats = []
        for section_name, cat in cls.category_paths:
            if cat not in cats:
                cats.append(cat)
        return cats

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        extra_args = extra_args or {}
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = extra_args.get(
            "user_agent", cls.DEFAULT_USER_AGENT
        )
        session.headers["tenant"] = cls.tenant
        product_urls = []

        query_url = (
            "https://529cv9h7mw-dsn.algolia.net/1/indexes/*/"
            "queries?x-algolia-application-id=529CV9H7MW&x-"
            "algolia-api-key=c6ab9bc3e19c260e6bad42abe143d5f4"
        )

        query_params = {
            "requests": [
                {
                    "indexName": "campaigns_production",
                    "params": "query={}&hitsPerPage=1000".format(keyword),
                }
            ]
        }

        response = session.post(query_url, json.dumps(query_params))
        data = json.loads(response.text)

        if not data["results"][0]["hits"]:
            return []

        for entry in data["results"][0]["hits"]:
            product_url = "https://www.lider.cl/catalogo/product/sku/{}/{}".format(
                entry["sku"], entry.get("slug", "a")
            )
            product_urls.append(product_url)

            if len(product_urls) == threshold:
                return product_urls

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        extra_args = extra_args or {}
        session = session_with_proxy(extra_args)
        session.headers = {
            "User-Agent": extra_args.get("user_agent", cls.DEFAULT_USER_AGENT),
            "tenant": cls.tenant,
        }
        sku_id = url.split("/")[-2]

        query_url = "https://apps.lider.cl/catalogo/bff/products/{}".format(sku_id)

        response = session.get(query_url)

        if response.status_code in [500]:
            parsed_extra_args = extra_args or {}
            retries = parsed_extra_args.pop("retries", 5)

            if retries:
                time.sleep(5)
                parsed_extra_args["retries"] = retries - 1
                return cls.products_for_url(
                    url, category=category, extra_args=parsed_extra_args
                )
            else:
                return []

        entry = json.loads(response.text)

        if not entry.get("success", True):
            return []

        name = "{} {}".format(entry["brand"], entry["displayName"])
        ean = entry["gtin13"]

        if not check_ean13(ean):
            ean = None

        key = str(entry["sku"])
        sku = entry["itemNumber"]
        normal_price = Decimal(entry["price"]["BasePriceSales"]).quantize(
            Decimal("1.00")
        )
        offer_price_container = entry["price"]["BasePriceTLMC"]

        if offer_price_container:
            offer_price = Decimal(offer_price_container)
            if not offer_price:
                offer_price = normal_price

            if offer_price > normal_price:
                offer_price = normal_price
        else:
            offer_price = normal_price

        specs = OrderedDict()
        for spec in entry.get("filters", []):
            specs.update(spec)

        part_number = specs.get("Modelo")
        if part_number:
            part_number = part_number[:49]

        description = None
        if "longDescription" in entry:
            description = entry["longDescription"]

        if description:
            description = html_to_markdown(description)

        picture_urls = [
            img for img in entry["images"]["availableImages"] if validators.url(img)
        ]

        if "REACONDICIONADO" in name.upper():
            condition = "https://schema.org/RefurbishedCondition"
        else:
            condition = "https://schema.org/NewCondition"

        seller = entry.get("winningOffer", {}).get("sellerName", None) or None

        if seller:
            stock = 0
        elif entry["available"]:
            stock = -1
        else:
            stock = 0

        # The preflight method verified that the LiveChat widget is being
        # loaded, and the Google Tag Manager logic that Lider uses to trigger
        # the wiodget makes sure that we only need to check for the brand.
        has_virtual_assistant = entry["brand"] == "LG"

        return [
            Product(
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
                ean=ean,
                part_number=part_number,
                picture_urls=picture_urls,
                description=description,
                has_virtual_assistant=has_virtual_assistant,
                condition=condition,
                seller=seller,
            )
        ]

    @classmethod
    def banners(cls, extra_args=None):
        extra_args = extra_args or {}
        base_url = "https://apps.lider.cl/catalogo/bff/banners?v=2"
        destination_url_base = "https://www.lider.cl/{}"
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = cls.DEFAULT_USER_AGENT
        banners = []
        response = session.get(base_url)

        banners_json = json.loads(response.text)
        sliders = banners_json["bannersHome"]

        for idx, slider in enumerate(sliders):
            destination_urls = [destination_url_base.format(slider["link"])[:250]]
            picture_url = slider["backgroundDesktop"]

            banners.append(
                {
                    "url": destination_url_base.format(""),
                    "picture_url": picture_url,
                    "destination_urls": destination_urls,
                    "key": picture_url,
                    "position": idx + 1,
                    "section": bs.HOME,
                    "subsection": "Home",
                    "type": bs.SUBSECTION_TYPE_HOME,
                }
            )

        return banners
