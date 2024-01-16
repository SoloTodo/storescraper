import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    KEYBOARD,
    NOTEBOOK,
    RAM,
    PROCESSOR,
    PRINTER,
    MONITOR,
    MOTHERBOARD,
    HEADPHONES,
    VIDEO_CARD,
    SOLID_STATE_DRIVE,
    EXTERNAL_STORAGE_DRIVE,
    MOUSE,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Eylstore(StoreWithUrlExtensions):
    preferred_products_for_url_concurrency = 3

    url_extensions = [
        ["discos-externos", EXTERNAL_STORAGE_DRIVE],
        ["disco-nvme", SOLID_STATE_DRIVE],
        # ["discos-ssd", SOLID_STATE_DRIVE],
        ["memorias-ram", RAM],
        ["placas-madres", MOTHERBOARD],
        ["procesadores", PROCESSOR],
        ["tarjetas-de-video", VIDEO_CARD],
        ["audifonos-gaming", HEADPHONES],
        ["monitores-gaming", MONITOR],
        ["mouse-gaming", MOUSE],
        ["teclados-gaming", KEYBOARD],
        ["impresoras-laser", PRINTER],
        ["impresoras-tinta", PRINTER],
        ["monitores", MONITOR],
        ["gaming-notebooks", NOTEBOOK],
        ["oficina", NOTEBOOK],
        ["ultra-livianos", NOTEBOOK],
        ["workstation", NOTEBOOK],
        ["audifonos", HEADPHONES],
        ["mouse", MOUSE],
        ["teclados", KEYBOARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        session.headers[
            "Content-Type"
        ] = "application/x-www-form-urlencoded; charset=UTF-8"

        url = "https://eylstore.cl/categoria-producto/{}".format(url_extension)
        res = session.get(url)
        print(url)
        soup = BeautifulSoup(res.text, "html.parser")

        product_urls = []
        widget_tags = soup.findAll(
            "div", {"data-widget_type": "uael-woo-products.grid-franko"}
        )
        if len(widget_tags) > 1:
            widget_id = widget_tags[0]["data-id"]
            match = re.search(r'"get_product_nonce":"(.+?)"', res.text)
            nonce = match.groups()[0]
            page_tag = soup.find("div", {"data-elementor-type": "product-archive"})
            page_id = page_tag["data-elementor-id"]
            page = 1
            while True:
                if page > 20:
                    raise Exception("page overflow: " + url_extension)
                payload = (
                    "action=uael_get_products&page_id={}&skin=grid_franko&"
                    "widget_id={}&page_number={}"
                    "&nonce={}"
                ).format(page_id, widget_id, page, nonce)
                res = session.post(
                    "https://eylstore.cl/wp-admin/admin-ajax.php", payload
                )

                soup = BeautifulSoup(res.json()["data"]["html"], "html.parser")
                product_containers = soup.findAll("li", "product-type-simple")

                if not product_containers:
                    break

                for container in product_containers:
                    product_url = container.find("a")["href"]
                    product_urls.append(product_url)
                page += 1
        else:
            products_containers = soup.findAll("div", "uael-woo-products-inner")
            if len(products_containers) == 1:
                return []

            for container in products_containers[0].findAll(
                "li", "product-type-simple"
            ):
                product_url = container.find("a")["href"]
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        name = soup.find("h1", "product_title").text.strip()
        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
        sku_tag = soup.find("span", "sku")

        if sku_tag:
            sku = soup.find("span", "sku").text.strip()
        else:
            sku = None

        stock_tag = soup.find("p", "in-stock")
        if stock_tag:
            stock = int(re.search(r"(\d+)", stock_tag.text).groups()[0])
        else:
            stock = 0

        pricing_tag = soup.find("div", "elementor-widget-woocommerce-product-price")
        price_tag = pricing_tag.findAll("span", "woocommerce-Price-amount")[-1]
        price = Decimal(remove_words(price_tag.text))

        picture_urls = []
        picture_container = soup.find("div", "woocommerce-product-gallery__wrapper")
        for a in picture_container.findAll("a"):
            picture_urls.append(a["href"])

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
            part_number=sku,
        )
        return [p]
