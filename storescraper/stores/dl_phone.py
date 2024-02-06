import json
from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import (
    CELL,
    HEADPHONES,
    NOTEBOOK,
    TABLET,
    WEARABLE,
    TELEVISION,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class DLPhone(StoreWithUrlExtensions):
    url_extensions = [
        ["audifonos", HEADPHONES],
        ["celulares-2", CELL],
        ["celulares", CELL],
        ["celulares-samsung", CELL],
        ["celulares-huawei", CELL],
        ["celulares-motorola", CELL],
        ["oppo", CELL],
        ["ipad", TABLET],
        ["ipad-y-tablet-2-apple", TABLET],
        ["tablet-samsung", TABLET],
        ["tablet-huawei", TABLET],
        ["notebooks", NOTEBOOK],
        ["computacion-huawei", NOTEBOOK],
        ["smartwhatch", WEARABLE],
        ["televisores", TELEVISION],
        ["hisense", TELEVISION],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        url_webpage = "https://www.dlphone.cl/{}/".format(url_extension)
        print(url_webpage)
        response = session.get(url_webpage)
        soup = BeautifulSoup(response.text, "html.parser")
        product_containers = soup.findAll("li", "product")

        if not product_containers:
            logging.warning("empty category: " + url_extension)
        for container in product_containers:
            product_url = container.find("a")["href"]
            product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        gtm_data = json.loads(
            soup.find("input", {"name": "gtm4wp_product_data"})["value"]
        )
        name = gtm_data["item_name"]
        key = str(gtm_data["internal_id"])
        sku = str(gtm_data["item_id"])
        price = Decimal(gtm_data["price"])
        stock = gtm_data["stocklevel"]
        picture_urls = [
            x.find("a")["href"]
            for x in soup.findAll("div", "woocommerce-product-gallery__image")
        ]
        description = html_to_markdown(
            str(soup.find("div", "woocommerce-product-details__short-description"))
        )

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
            condition="https://schema.org/RefurbishedCondition",
        )
        return [p]
