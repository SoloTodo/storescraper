import html
import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    MONITOR,
    NOTEBOOK,
    TABLET,
    MOUSE,
    VIDEO_GAME_CONSOLE,
    CELL,
    TELEVISION,
)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class UltraPc(StoreWithUrlExtensions):
    url_extensions = [
        ["equipos-de-computo", NOTEBOOK],
        ["tablets-e-ipads", TABLET],
        ["monitores", MONITOR],
        ["accesorios", MOUSE],
        ["consolas-videojuegos", VIDEO_GAME_CONSOLE],
        ["smartphones-2", CELL],
        ["electrodomesticos", TELEVISION],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        product_urls = []
        url_webpage = "https://www.ultrapc.cl/categoria-producto/{}/" "?ppp=-1".format(
            url_extension
        )
        print(url_webpage)
        response = session.get(url_webpage)
        soup = BeautifulSoup(response.text, "lxml")
        products_container = soup.find("ul", "products")

        if not products_container:
            return []

        for cont in products_container.findAll("div", "product-outer"):
            product_url = cont.find("a", "woocommerce-LoopProduct-link")["href"]
            product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        base_name = soup.find("h1", "product_title").text

        bundle_tag = soup.find("span", "accesorios_sumario")
        if bundle_tag:
            base_name += " BUNDLE: " + " ".join(bundle_tag["data-tooltip"].split())

        variants = soup.find("form", "variations_form")
        products = []

        if variants:
            container_products = json.loads(
                html.unescape(variants["data-product_variations"])
            )

            for product in container_products:
                variant_name = (
                    base_name + " - " + next(iter(product["attributes"].values()))
                )
                if product["is_in_stock"]:
                    stock = int(product["max_qty"])
                else:
                    stock = 0
                sku = product["sku"]
                key = str(product["variation_id"])
                price = Decimal(product["display_price"])
                if product["image"]["src"] == "":
                    picture_urls = [
                        "https://www.ultrapc.cl" + tag["src"]
                        for tag in soup.find(
                            "div", "woocommerce-product-gallery"
                        ).findAll("img")
                    ]
                else:
                    picture_urls = [product["image"]["src"]]
                products.append(
                    Product(
                        variant_name,
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
                    )
                )
        else:
            key = soup.find("link", {"type": "application/json"})["href"].split("/")[-1]
            sku = soup.find("meta", {"property": "product:retailer_item_id"})["content"]
            description_tag = soup.find("div", {"id": "tab-description"})
            description = html_to_markdown(str(description_tag)).split("————————")[1]

            product_container = soup.find("div", "post-" + key)

            query_stock_button = soup.find("div", "boton_consultar_stock")

            if query_stock_button:
                stock = 0
            else:
                blacklist = [
                    "outofstock",
                    "product_tag-proximamente",
                    "product_tag-reservado",
                ]

                for keyword in blacklist:
                    if keyword in product_container.attrs["class"]:
                        stock = 0
                        break
                else:
                    stock = -1

            price_tags = soup.findAll("span", "precio_oferta")
            if not price_tags:
                price_tags = soup.findAll("span", "precio_con_iva_tbk")

            assert len(price_tags) in [1, 2]

            if len(price_tags) == 1:
                price_tags.append(price_tags[0])

            normal_price = Decimal(remove_words(price_tags[1].text))
            offer_price = Decimal(remove_words(price_tags[0].text))

            picture_urls = [
                "https://www.ultrapc.cl/" + tag["src"]
                for tag in soup.find("div", "woocommerce-product-gallery").findAll(
                    "img"
                )
            ]

            condition_span = soup.find("span", "condicion_item_ultrapc")
            condition = "https://schema.org/NewCondition"
            conditions_dict = {
                "NUEVO": "https://schema.org/NewCondition",
                "NUEVO SELLADO": "https://schema.org/NewCondition",
                "USADO": "https://schema.org/UsedCondition",
                "SEMINUEVO": "https://schema.org/UsedCondition",
                "OPEN BOX": "https://schema.org/OpenBoxCondition",
                "REACONDICIONADO (SIN USO)": "https://schema.org/RefurbishedCondition",
            }
            if condition_span:
                condition_text = condition_span.text.strip().upper()
                condition = conditions_dict[condition_text]

            products.append(
                Product(
                    base_name,
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
                    picture_urls=picture_urls,
                    condition=condition,
                    description=description,
                    allow_zero_prices=True,
                )
            )
        return products
