import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    MOTHERBOARD,
    NOTEBOOK,
    RAM,
    VIDEO_CARD,
    SOLID_STATE_DRIVE,
    PROCESSOR,
    MONITOR,
    MOUSE,
    CPU_COOLER,
    POWER_SUPPLY,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class SamuraiStore(StoreWithUrlExtensions):
    url_extensions = [
        ["perifericos", MOUSE],
        ["fuentes-de-poder", POWER_SUPPLY],
        ["cooler-cpu", CPU_COOLER],
        ["placas-madre", MOTHERBOARD],
        ["monitor", MONITOR],
        ["notebooks", NOTEBOOK],
        ["procesador", PROCESSOR],
        ["ram", RAM],
        ["ram-notebook", RAM],
        ["tarjetas-de-video", VIDEO_CARD],
        ["unidades-de-almacenamiento", SOLID_STATE_DRIVE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 50:
                raise Exception("page overflow: " + url_extension)
            url_webpage = (
                "https://www.samuraistorejp.cl/shop/page/{}/?product-category={}"
            ).format(page, url_extension)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("div", "product-small")
            if not product_containers or soup.find("section", "error-404"):
                if page == 1:
                    logging.warning("Empty category: {}".format(url_extension))
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

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, "lxml")
        name_tag = soup.find("h1", "product-title")

        if not name_tag:
            return []

        name = name_tag.text.strip()

        if "RIFA" in name:
            return []

        key = soup.find("link", {"rel": "shortlink"})["href"].split("p=")[-1]
        sku_tag = soup.find("span", "sku")

        if sku_tag:
            sku = sku_tag.text.strip()
        else:
            sku = None

        tags_label = soup.find("span", "tagged_as")

        if not tags_label:
            return []

        tags = tags_label.findAll("a")

        for tag in tags:
            tag_text = tag.text.upper()
            if "ENTREGA INMEDIATA" in tag_text:
                available_for_purchase = True
                description_prefix = "ENTREGA INMEDIATA"
                break
            elif "STOCK ONLINE" in tag_text:
                available_for_purchase = False
                description_prefix = "STOCK ONLINE"
                break
            elif "IMPORTADO" in tag_text:
                available_for_purchase = False
                description_prefix = "IMPORTADO"
                break
        else:
            raise Exception("No valid tag found")

        description = (
            description_prefix
            + " "
            + html_to_markdown(
                str(soup.find("div", "woocommerce-Tabs-panel--description"))
            )
            + " "
            + html_to_markdown((str(soup.find("div", "product-short-description"))))
        )

        if not available_for_purchase:
            stock = 0
        elif "preventa" in name.lower():
            stock = 0
        elif soup.find("p", "available-on-backorder"):
            stock = 0
        elif soup.find("p", "stock out-of-stock"):
            stock = 0
        elif soup.find("p", "stock in-stock"):
            stock = int(soup.find("p", "stock in-stock").text.split()[0])
        else:
            stock = -1

        price_p = soup.find("p", "product-page-price")
        if not price_p:
            return []
        price_containers = price_p.findAll("span", "woocommerce-Price-amount")

        if not price_containers:
            return []

        offer_price = Decimal(remove_words(price_containers[-1].text))
        normal_price = (offer_price * Decimal("1.04")).quantize(0)

        picture_urls = [
            tag.find("a")["href"]
            for tag in soup.find("div", "product-gallery").findAll(
                "div", "woocommerce-product-gallery__image"
            )
        ]
        picture_urls = list(filter(None, picture_urls))

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
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
