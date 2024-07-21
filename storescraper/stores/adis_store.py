from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import *
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class AdisStore(StoreWithUrlExtensions):
    url_extensions = [
        ["452-tarjeta_sd", MEMORY_CARD],
        ["511-notebook", NOTEBOOK],
        ["512-probook", NOTEBOOK],
        ["513-aio_todo_en_uno", ALL_IN_ONE],
        ["514-disco_duro_interno", STORAGE_DRIVE],
        ["515-memoria_ram", RAM],
        ["516-pendrive", USB_FLASH_DRIVE],
        ["517-disco_estado_solido", SOLID_STATE_DRIVE],
        ["518-laptop", NOTEBOOK],
        ["519-teclado", KEYBOARD],
        ["520-elitebook", NOTEBOOK],
        ["521-combo_teclado_y_mouse", KEYBOARD_MOUSE_COMBO],
        ["523-monitor", MONITOR],
        ["526-kit_teclado_y_mouse", KEYBOARD_MOUSE_COMBO],
        ["529-mouse_gamer", MOUSE],
        ["530-teclado_gamer", KEYBOARD],
        ["531-tablet", TABLET],
        ["532-procesador", PROCESSOR],
        ["533-mouse_inalambrico", MOUSE],
        ["534-memoria_ram_para_servidor", RAM],
        ["539-juego_de_teclado_y_raton", KEYBOARD_MOUSE_COMBO],
        ["540-teclado_mp_com", KEYBOARD],
        ["542-disco_duro", STORAGE_DRIVE],
        ["544-ps2usb", MOUSE],
        ["546-refrigeracion_para_procesador", CPU_COOLER],
        ["548-disco_duro_para_servidor", STORAGE_DRIVE],
        ["550-parlante", STEREO_SYSTEM],
        ["392-memoria_ram", RAM],
        ["393-fuente_de_poder", POWER_SUPPLY],
        ["394-disco_estado_solido", SOLID_STATE_DRIVE],
        ["395-gabinete", COMPUTER_CASE],
        ["396-tarjeta_madre", MOTHERBOARD],
        ["397-mouse_cableado", MOUSE],
        ["398-refrigeracion_liquida_para_procesador", CPU_COOLER],
        ["399-audifonos", HEADPHONES],
        ["400-tarjeta_de_video", VIDEO_CARD],
        ["401-tarjeta_micro_sd", MEMORY_CARD],
        ["403-teclado", KEYBOARD],
        ["404-ssd_disco_de_estado_solido", SOLID_STATE_DRIVE],
        ["406-tarjeta_sd", MEMORY_CARD],
        ["501-disco_duro", STORAGE_DRIVE],
        ["502-placa_madre", MOTHERBOARD],
        ["505-power_supply", POWER_SUPPLY],
        ["508-pendrive", USB_FLASH_DRIVE],
        ["509-procesador", PROCESSOR],
        ["408-tarjetas_de_memoria_flash", MEMORY_CARD],
        ["410-prendrive", USB_FLASH_DRIVE],
        ["562-ipad", TABLET],
        ["563-macbook", NOTEBOOK],
        ["564-imac", ALL_IN_ONE],
        ["566-teclado_apple", KEYBOARD],
        ["567-audifonos", HEADPHONES],
        ["568-mouse_inalambrico", MOUSE],
        ["570-notebook", NOTEBOOK],
        ["571-tablet", TABLET],
        ["572-reloj_watch", WEARABLE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            url_webpage = "https://adis-store.cl/{}?page={}".format(url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.find("div", {"id": "js-product-list"}).findAll(
                "article", "product-miniature"
            )
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = container.find("a")["href"]
                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        if response.status_code == 500:
            return []
        soup = BeautifulSoup(response.text, "lxml")

        json_tag = soup.find("div", "js-product-details")
        json_data = json.loads(json_tag["data-product"])
        name = json_data["name"]
        key = str(json_data["id"])
        stock = json_data["quantity"]
        price = Decimal(json_data["price_amount"])
        part_number = json_data["reference"]
        picture_urls = [
            image["bySize"]["large_default"]["url"] for image in json_data["images"]
        ]
        description = html_to_markdown(json_data["description"])

        p = Product(
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
            sku=part_number,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number,
        )
        return [p]
