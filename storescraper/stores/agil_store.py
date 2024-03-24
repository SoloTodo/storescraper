from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    MONITOR,
    MOUSE,
    NOTEBOOK,
    POWER_SUPPLY,
    PROCESSOR,
    STORAGE_DRIVE,
    TABLET,
    PRINTER,
    ALL_IN_ONE,
    KEYBOARD_MOUSE_COMBO,
    EXTERNAL_STORAGE_DRIVE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import remove_words, session_with_proxy, html_to_markdown


class AgilStore(StoreWithUrlExtensions):
    url_extensions = [
        ["5507", PRINTER],  # Impresoras
        ["5553", NOTEBOOK],  # Laptop
        ["5554", ALL_IN_ONE],  # All in One
        ["5558", TABLET],  # Tablet
        ["5570", KEYBOARD_MOUSE_COMBO],  # Kit Mouse y Teclado
        ["5572", MOUSE],  # Mouse
        ["5593", MONITOR],  # Monitor
        ["5663", PROCESSOR],  # Procesador
        ["5601", STORAGE_DRIVE],  # Disco Duro Interno
        ["5602", EXTERNAL_STORAGE_DRIVE],  # Disco Duro Externo
        ["5606", POWER_SUPPLY],  # Fuente Poder
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        url_webpage = (
            "https://www.agilstore.cl/productos.php?ver=productos&id={}".format(
                url_extension
            )
        )
        print(url_webpage)
        response = session.get(url_webpage, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        product_containers = soup.findAll("div", "product")

        if not product_containers:
            logging.warning("empty category: " + url_extension)

        for container in product_containers:
            product_url = "https://www.agilstore.cl/" + container.find("a")["href"]
            product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        name = soup.find("h2", "product-name").text.strip()
        key = soup.find("input", {"name": "id_producto"})["value"]
        stock = -1
        price = Decimal(remove_words(soup.find("h3", "product-price").contents[-1]))
        sku_label = soup.find("strong", text="Código")
        sku = sku_label.next.next[2:]
        pn_label = soup.find("strong", text="Part Number Fabricante")
        part_number = pn_label.next.next[2:]
        picture_urls = [soup.find("div", {"id": "product-main-img"}).find("img")["src"]]
        description = html_to_markdown(str(soup.find("div", "product-details")))

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
            part_number=part_number,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
