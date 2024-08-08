import logging
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    GAMING_CHAIR,
    HEADPHONES,
    MEMORY_CARD,
    USB_FLASH_DRIVE,
    ALL_IN_ONE,
    WEARABLE,
    CPU_COOLER,
    KEYBOARD,
    KEYBOARD_MOUSE_COMBO,
    MOUSE,
    NOTEBOOK,
    MONITOR,
    TABLET,
    VIDEO_CARD,
    RAM,
    CELL,
    STORAGE_DRIVE,
    SOLID_STATE_DRIVE,
    PROCESSOR,
    MOTHERBOARD,
    COMPUTER_CASE,
    POWER_SUPPLY,
    PRINTER,
    EXTERNAL_STORAGE_DRIVE,
    STEREO_SYSTEM,
    UPS,
)
from storescraper.flixmedia import flixmedia_video_urls
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import (
    remove_words,
    html_to_markdown,
    cf_session_with_proxy,
)


class Winpy(StoreWithUrlExtensions):
    url_extensions = [
        ["portatiles/notebooks/", NOTEBOOK],
        ["portatiles/mobile-workstation/", NOTEBOOK],
        ["zona-notebook-gamers/", NOTEBOOK],
        ["portatiles/celulares/", CELL],
        ["portatiles/tablet/", TABLET],
        ["memorias/para-notebook/", RAM],
        ["almacenamiento/disco-estado-solido/", SOLID_STATE_DRIVE],
        ["almacenamiento/disco-duro-notebook/", STORAGE_DRIVE],
        ["computadores/todo-en-uno/", ALL_IN_ONE],
        ["memorias/para-computadores/", RAM],
        ["almacenamiento/disco-duro-pc-s/", STORAGE_DRIVE],
        ["partes-y-piezas/tarjetas-de-video/", VIDEO_CARD],
        ["accesorios/mouse/", MOUSE],
        ["accesorios/teclados/", KEYBOARD],
        ["accesorios/kit-perifericos/", KEYBOARD_MOUSE_COMBO],
        ["partes-y-piezas/placas-madres/", MOTHERBOARD],
        ["partes-y-piezas/procesadores/", PROCESSOR],
        ["memorias/", RAM],
        ["partes-y-piezas/gabinetes/", COMPUTER_CASE],
        ["partes-y-piezas/fuente-de-poder/", POWER_SUPPLY],
        ["partes-y-piezas/disipadores/", CPU_COOLER],
        ["accesorios/sillas-y-mesas/", GAMING_CHAIR],
        ["almacenamiento/nas/", STORAGE_DRIVE],
        ["almacenamiento/discos-portatiles/", EXTERNAL_STORAGE_DRIVE],
        ["almacenamiento/discos-sobremesa/", EXTERNAL_STORAGE_DRIVE],
        ["almacenamiento/memorias-flash/", MEMORY_CARD],
        ["almacenamiento/pendrive/", USB_FLASH_DRIVE],
        ["apple/imac/", ALL_IN_ONE],
        ["apple/macbook-pro-retina/", NOTEBOOK],
        ["apple/ipad/", TABLET],
        ["apple/watch/", WEARABLE],
        ["monitores/", MONITOR],
        ["impresoras/", PRINTER],
        ["accesorios/audifonos/", HEADPHONES],
        ["accesorios/parlantes/", STEREO_SYSTEM],
        ["ups/ups/", UPS],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        base_url = "https://www.winpy.cl"
        product_urls = []
        session = cf_session_with_proxy(extra_args)
        url = base_url + "/" + url_extension

        page = 1
        while True:
            if page >= 40:
                raise Exception("Page overflow: " + url_extension)

            url_with_page = url + "paged/" + str(page) + "/"
            print(url_with_page)
            soup = BeautifulSoup(session.get(url_with_page).text, "html5lib")
            product_containers = soup.find("section", {"id": "productos"})
            product_containers = product_containers.findAll("article")

            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break

            for container in product_containers:
                product_url = "https://www.winpy.cl" + container.find("a")["href"]
                product_urls.append(product_url)

            if not soup.find("div", "paginador"):
                break

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = cf_session_with_proxy(extra_args)
        response = session.get(url)

        if response.url != url or response.status_code == 404:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, "html5lib")

        name = soup.find("h1", {"itemprop": "name"}).text.strip()
        part_number = soup.find("span", "sku").text.strip()
        sku = part_number

        condition_str = soup.find("span", {"itemprop": "itemCondition"}).text.strip()

        condition_dict = {
            "NUEVO": "https://schema.org/NewCondition",
            "REEMBALADO": "https://schema.org/RefurbishedCondition",
            "REACONDICIONADO": "https://schema.org/RefurbishedCondition",
            "SEMI-NUEVO": "https://schema.org/RefurbishedCondition",
            "USADO": "https://schema.org/UsedCondition",
            "DE SHOW ROOM": "https://schema.org/RefurbishedCondition",
            "OUTLET": "https://schema.org/RefurbishedCondition",
            "EMBALAJE DAÑADO": "https://schema.org/OpenBoxCondition",
        }

        condition = condition_dict[condition_str]
        if sku.endswith(".PLUS"):
            condition = "https://schema.org/RefurbishedCondition"

        if soup.find("div", "sinstock"):
            stock = 0
            normal_price = Decimal(
                remove_words(
                    soup.find("meta", {"property": "product:price:amount"})["content"]
                )
            )
            offer_price = normal_price
        else:
            stock = int(soup.find("p", {"itemprop": "offerCount"}).text)

            offer_price = Decimal(
                remove_words(soup.find("p", {"itemprop": "lowPrice"}).string)
            )

            normal_price = Decimal(
                remove_words(soup.find("p", {"itemprop": "highPrice"}).string)
            )

        if not normal_price or not offer_price:
            return []

        description = html_to_markdown(str(soup.find("div", "info")))

        picture_tags = soup.findAll("img", {"itemprop": "image"})

        picture_urls = [
            "https://www.winpy.cl" + urllib.parse.quote(tag["src"])
            for tag in picture_tags
        ]

        flixmedia_id = None
        video_urls = None
        flixmedia_tag = soup.find(
            "script", {"src": "//media.flixfacts.com/js/loader.js"}
        )

        if flixmedia_tag:
            try:
                flixmedia_id = flixmedia_tag["data-flix-mpn"]
                video_urls = flixmedia_video_urls(flixmedia_id)
            except KeyError:
                pass

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
            part_number=part_number,
            condition=condition,
            description=description,
            picture_urls=picture_urls,
            flixmedia_id=flixmedia_id,
            video_urls=video_urls,
        )

        return [p]
