import logging
from collections import defaultdict

from bs4 import BeautifulSoup
from decimal import Decimal
from urllib.parse import urlparse, parse_qs, urlencode

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
            "Tecnología / Computadores",
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
                "https://www.abcdin.cl/on/demandware.store/Sites-Abcdin-Site/es_CL/Search-UpdateGrid?cgid={}&"
                "srule=best-matches&sz=1000"
            ).format(category_id)
            print(url)

            res = session.get(url)
            soup = BeautifulSoup(res.text, "html.parser")
            product_cells = soup.findAll("div", "product-tile__item")

            if not product_cells:
                raise Exception("Empty category: " + category_id)

            for idx, product_cell in enumerate(product_cells):
                product_path = product_cell.find("a", "image-link")["href"]
                product_url = "https://www.abcdin.cl" + product_path
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
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        product_urls = []

        keyword = keyword.replace(" ", "+")

        url = (
            "https://www.abcdin.cl/tienda/ProductListingView?"
            "ajaxStoreImageDir=%2Fwcsstore%2FABCDIN%2F&searchType=10"
            "&resultCatEntryType=2&searchTerm={}&resultsPerPage=24"
            "&sType=SimpleSearch&disableProductCompare=false"
            "&catalogId=10001&langId=-1000&enableSKUListView=false"
            "&ddkey=ProductListingView_6_-2011_1410&storeId=10001"
            "&pageSize=1000".format(keyword)
        )

        soup = BeautifulSoup(session.get(url).text, "html.parser")
        products_grid = soup.find("ul", "grid_mode")

        if not products_grid:
            return []

        product_cells = products_grid.findAll("li")

        for product_cell in product_cells:
            product_listed_url = product_cell.find("a")["href"]
            if "ProductDisplay" in product_listed_url:
                parsed_product = urlparse(product_listed_url)
                parameters = parse_qs(parsed_product.query)

                parameters = {
                    k: v for k, v in parameters.items() if k in ["productId", "storeId"]
                }

                newqs = urlencode(parameters, doseq=True)

                product_url = (
                    "https://www.abcdin.cl/tienda/es/abcdin/" "ProductDisplay?" + newqs
                )
            else:
                slug_with_sku = product_listed_url.split("/")[-1]
                product_url = "https://www.abcdin.cl/tienda/es/abcdin/" + slug_with_sku

            product_urls.append(product_url)

            if len(product_urls) == threshold:
                return product_urls

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        name = soup.find("h1", {"itemprop": "name"}).text.strip()
        key = soup.find("span", {"itemprop": "sku"})["data-sku"]
        price = Decimal(soup.find("span", "price-value")["data-value"]).quantize(
            Decimal(0)
        )
        stock = -1
        sku = soup.find("span", "cod").text.split(":")[1].strip()
        description = html_to_markdown(str(soup.find("div", "description-and-detail")))
        picture_urls = [
            x.find("img")["src"] for x in soup.findAll("div", "primary-image")
        ]

        product = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
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
        base_url = "https://www.abcdin.cl/{}"

        sections_data = [
            [bs.HOME, "Home", bs.SUBSECTION_TYPE_HOME, ""],
            [bs.ELECTRO_ABCDIN, "Electro", bs.SUBSECTION_TYPE_CATEGORY_PAGE, "electro"],
            [
                bs.ELECTRO_ABCDIN,
                "Electro / TV y Video",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro/tv-y-video",
            ],
            [
                bs.ELECTRO_ABCDIN,
                "Electro / Audio",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro/audio",
            ],
            [
                bs.ELECTRO_ABCDIN,
                "Electro / Audífonos",
                bs.SUBSECTION_TYPE_MOSAIC,
                "electro/audifonos",
            ],
            [
                bs.LINEA_BLANCA_ABCDIN,
                "Línea Blanca",
                bs.SUBSECTION_TYPE_CATEGORY_PAGE,
                "linea-blanca",
            ],
            [
                bs.LINEA_BLANCA_ABCDIN,
                "Línea Blanca / Climatización",
                bs.SUBSECTION_TYPE_CATEGORY_PAGE,
                "linea-blanca/climatizacion",
            ],
            [
                bs.LINEA_BLANCA_ABCDIN,
                "Línea Blanca / Refrigeradores",
                bs.SUBSECTION_TYPE_CATEGORY_PAGE,
                "linea-blanca/refrigeradores",
            ],
            [
                bs.LINEA_BLANCA_ABCDIN,
                "Línea Blanca / Electrodomésticos",
                bs.SUBSECTION_TYPE_CATEGORY_PAGE,
                "linea-blanca/electrodomesticos",
            ],
            [
                bs.TELEFONIA_ABCDIN,
                "Telefonía",
                bs.SUBSECTION_TYPE_CATEGORY_PAGE,
                "telefonia",
            ],
            [
                bs.TELEFONIA_ABCDIN,
                "Telefonía / Smartphones",
                bs.SUBSECTION_TYPE_MOSAIC,
                "telefonia/smartphones",
            ],
            [
                bs.TELEFONIA_ABCDIN,
                "Telefonía / Smartwatch",
                bs.SUBSECTION_TYPE_MOSAIC,
                "telefonia/smartwatch",
            ],
            [
                bs.TELEFONIA_ABCDIN,
                "Telefonía / Accesorios telefonía",
                bs.SUBSECTION_TYPE_MOSAIC,
                "telefonia/accesorios-telefonia",
            ],
            [
                bs.COMPUTACION_ABCDIN,
                "Computación",
                bs.SUBSECTION_TYPE_CATEGORY_PAGE,
                "computacion",
            ],
            [
                bs.COMPUTACION_ABCDIN,
                "Computación / Notebooks",
                bs.SUBSECTION_TYPE_MOSAIC,
                "computacion/notebooks",
            ],
            [
                bs.COMPUTACION_ABCDIN,
                "Computación / Tablets",
                bs.SUBSECTION_TYPE_MOSAIC,
                "computacion/tablets",
            ],
            [
                bs.COMPUTACION_ABCDIN,
                "Computación / Accesorios Computación",
                bs.SUBSECTION_TYPE_MOSAIC,
                "computacion/accesorios-computacion",
            ],
            [
                bs.COMPUTACION_ABCDIN,
                "Computación / Mundo Gamer",
                bs.SUBSECTION_TYPE_MOSAIC,
                "computacion/mundo-gamer",
            ],
            [
                bs.COMPUTACION_ABCDIN,
                "Computación / All In One",
                bs.SUBSECTION_TYPE_MOSAIC,
                "computacion/all-in-one",
            ],
            [
                bs.COMPUTACION_ABCDIN,
                "Computación / Monitores y Proyectores",
                bs.SUBSECTION_TYPE_MOSAIC,
                "computacion/monitores-y-proyectores",
            ],
            [
                bs.COMPUTACION_ABCDIN,
                "Computación / Monitores y Proyectores",
                bs.SUBSECTION_TYPE_MOSAIC,
                "computacion/monitores-y-proyectores",
            ],
            [
                bs.COMPUTACION_ABCDIN,
                "Computación / Almacenamiento",
                bs.SUBSECTION_TYPE_MOSAIC,
                "computacion/almacenamiento",
            ],
            [
                bs.COMPUTACION_ABCDIN,
                "Computación / Impresoras y Multifuncionales",
                bs.SUBSECTION_TYPE_MOSAIC,
                "computacion/impresoras-y-multifuncionales",
            ],
            [
                bs.ENTRETENIMIENTO_ABCDIN,
                "Entretenimiento",
                bs.SUBSECTION_TYPE_CATEGORY_PAGE,
                "entretenimiento",
            ],
            [
                bs.ENTRETENIMIENTO_ABCDIN,
                "Entretenimiento / Videojuegos",
                bs.SUBSECTION_TYPE_MOSAIC,
                "entretenimiento/videojuegos",
            ],
        ]

        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            print(url)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                soup = BeautifulSoup(
                    session.get("https://www.abcdin.cl/").text, "html.parser"
                )
                slider_tags = soup.find("div", "owl-carousel-custom-2").findAll("a")

                for index, slider_tag in enumerate(slider_tags):
                    destination_urls = ["https://www.abcdin.cl" + slider_tag["href"]]
                    picture_url = slider_tag.find("img")["data-src-desktop"]

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
                response = session.get(url)
                soup = BeautifulSoup(response.text, "html.parser")
                slider_container_tag = soup.find("div", "custom-slider")

                if not slider_container_tag:
                    logging.warning("Section without banners: " + url)
                    continue

                slider_tags = slider_container_tag.findAll("div", "banner-item")

                for index, slider_tag in enumerate(slider_tags):
                    if slider_tag.find("a"):
                        destination_urls = [
                            "https://www.abcdin.cl" + slider_tag.find("a")["href"]
                        ]
                    else:
                        destination_urls = []

                    image_tag = slider_tag.find("img")

                    if "data-src-desktop" not in image_tag.attrs:
                        continue

                    picture_url = image_tag["data-src-desktop"]
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
