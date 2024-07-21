import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    SOLID_STATE_DRIVE,
    COMPUTER_CASE,
    RAM,
    PROCESSOR,
    VIDEO_CARD,
    MOTHERBOARD,
    KEYBOARD,
    POWER_SUPPLY,
    CPU_COOLER,
    MONITOR,
    MOUSE,
    STORAGE_DRIVE,
    EXTERNAL_STORAGE_DRIVE,
    MICROPHONE,
    HEADPHONES,
    USB_FLASH_DRIVE,
    GAMING_CHAIR,
    CASE_FAN,
    NOTEBOOK,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy


class GWStore(StoreWithUrlExtensions):
    url_extensions = [
        ["3-procesadores", PROCESSOR],
        ["6-placas-madres", MOTHERBOARD],
        ["71-hdd", STORAGE_DRIVE],
        ["72-ssd-o-m2", SOLID_STATE_DRIVE],
        ["70-nvme", SOLID_STATE_DRIVE],
        ["73-disco-externo", EXTERNAL_STORAGE_DRIVE],
        ["82-memorias-ram", RAM],
        ["74-tarjetas-de-video", VIDEO_CARD],
        ["14-fuentes-de-poder", POWER_SUPPLY],
        ["81-gabinete", COMPUTER_CASE],
        ["44-mouse", MOUSE],
        ["45-teclados", KEYBOARD],
        ["47-microfonos", MICROPHONE],
        ["16-monitores", MONITOR],
        ["52-auriculares", HEADPHONES],
        ["93-pendrive", USB_FLASH_DRIVE],
        ["50-sillas", GAMING_CHAIR],
        ["78-refrigeracion-", CPU_COOLER],
        ["99-ventiladores-", CASE_FAN],
        ["112-notebook-", NOTEBOOK],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        )
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("page overflow: " + url_extension)
            url_webpage = "https://gwstore.cl/{}?" "page={}".format(url_extension, page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("article", "product-miniature")
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
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        key_input = soup.find("input", {"id": "product_page_product_id"})
        if not key_input:
            return []

        key = key_input["value"]
        name = soup.find("h1", "h1").text.strip()
        sku = soup.find("div", "product-reference").find("span").text.strip()
        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"]
        )
        picture_urls = [
            x["data-image-large-src"] for x in soup.findAll("img", "js-thumb")
        ]
        stock_div = soup.find("span", {"id": "product-availability"})

        if stock_div.find("i", "product-unavailable"):
            stock = 0
        else:
            stock = -1

        description = html_to_markdown(soup.find("div", "product-description").text)

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
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
