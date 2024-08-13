from bs4 import BeautifulSoup
from decimal import Decimal
import json
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import (
    CELL,
    NOTEBOOK,
)


class AFStore(StoreWithUrlExtensions):
    url_extensions = [
        ["iphone", CELL],
        ["lenovo", NOTEBOOK],
        ["mac", NOTEBOOK],
        ["samsung", CELL],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        page = 1

        while True:
            url = f"https://afstore.cl/categoria-producto/{url_extension}/page/{page}"
            print(url)
            response = session.get(url)

            if response.status_code == 404:
                if page == 1:
                    raise Exception("Invalid section: " + url)
                break

            soup = BeautifulSoup(response.text, "lxml")
            products = soup.findAll("li", "product__item")

            for product in products:
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, "lxml")
        base_name = soup.find("h1", "product__title").text.strip()
        description = html_to_markdown(soup.find("div", {"id": "tab-description"}).text)
        variations = soup.find("form", "variations_form")

        if not variations:
            product_data = json.loads(
                soup.find("script", {"type": "application/ld+json"}).text
            )
            key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
            sku = soup.find("span", "sku").text
            price = Decimal(product_data["offers"][0]["price"])

            stock_container = soup.find("p", "stock in-stock")

            stock = 0 if not stock_container else int(stock_container.text.split()[0])
            pictures_container = soup.find("div", "woocommerce-product-gallery")
            picture_urls = set(
                [img["src"] for img in pictures_container.findAll("img")]
            )

            p = Product(
                base_name,
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
                picture_urls=list(picture_urls),
            )

            return [p]

        products = []

        for variation in json.loads(variations.get("data-product_variations")):
            attributes = variation["attributes"]

            storage = (
                attributes.get(
                    "attribute_capacidad",
                )
                or attributes.get("attribute_almacenamiento")
                or None
            )
            color = attributes.get("attribute_color") or None
            condition_attribute = (
                attributes.get("attribute_estado-del-producto") or None
            )
            condition = None
            box = attributes.get("attribute_incluye-caja-original") or None

            name = base_name

            if storage:
                name += f" ({storage}"
            if color:
                name += f" / {color}"
            if condition_attribute:
                name += f" / {condition_attribute}"
                if condition_attribute == "Open Box":
                    condition = "https://schema.org/OpenBoxCondition"
                elif condition_attribute == "Vitrina":
                    condition = "https://schema.org/UsedCondition"

            if box:
                name += f" / {box}"

            if name != base_name:
                name += ")"

            key = str(variation["variation_id"])
            sku = variation["sku"]
            price = Decimal(variation["display_price"])
            stock = 0 if not variation["is_in_stock"] else variation["max_qty"] or -1
            picture_urls = [variation["image"]["url"]]

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
                condition=condition or "https://schema.org/NewCondition",
                description=description,
                picture_urls=picture_urls,
            )

            products.append(p)

        return products
