from bs4 import BeautifulSoup
from decimal import Decimal
import json
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import (
    CELL,
    HEADPHONES,
    NOTEBOOK,
    TELEVISION,
    VIDEO_GAME_CONSOLE,
    WEARABLE,
    ALL_IN_ONE,
)


class AFStore(StoreWithUrlExtensions):
    url_extensions = [
        ["airpods", HEADPHONES],
        ["imac", ALL_IN_ONE],
        ["macbook-air", NOTEBOOK],
        ["macbook-pro", NOTEBOOK],
        ["notebook", NOTEBOOK],
        ["consolas", VIDEO_GAME_CONSOLE],
        ["iphone", CELL],
        ["lenovo", NOTEBOOK],
        ["samsung", CELL],
        ["tv-hogar", TELEVISION],
        ["watch", WEARABLE],
        ["celulares", CELL],
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
            offer = product_data["offers"][0]
            key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
            sku_container = soup.find("span", "sku")
            sku = sku_container.text if sku_container else None
            price = Decimal(offer["price"])
            availability = offer.get("availability")
            stock_container = soup.find("p", "stock in-stock")

            if stock_container:
                stock = int(stock_container.text.split()[0])
            elif availability == "http://schema.org/InStock":
                stock = -1
            else:
                stock = 0

            picture_urls = [
                container.find("img")["src"]
                for container in soup.findAll("div", "wpgs_image")
            ]
            condition = (
                "https://schema.org/NewCondition"
                if "SELLADO" in description.upper()
                else "https://schema.org/OpenBoxCondition"
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
                part_number=sku if category == NOTEBOOK else None,
                condition=condition,
                description=description,
                picture_urls=picture_urls,
            )

            return [p]

        products = []

        for variation in json.loads(variations.get("data-product_variations")):
            attributes = variation["attributes"]
            name = f"{base_name} ({' / '.join(attributes.values())})"

            if (
                attributes.get("attribute_estado-del-producto", "").upper() == "SELLADO"
                or "SELLADO" in variation["variation_description"].upper()
            ):
                condition = "https://schema.org/NewCondition"
            else:
                condition = "https://schema.org/OpenBoxCondition"

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
                part_number=sku if category == NOTEBOOK else None,
                condition=condition,
                description=description,
                picture_urls=picture_urls,
            )

            products.append(p)

        return products
