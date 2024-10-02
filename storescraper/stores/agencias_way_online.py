from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, remove_words


from storescraper.categories import (
    TELEVISION,
    STEREO_SYSTEM,
    REFRIGERATOR,
    WASHING_MACHINE,
    STOVE,
    AIR_CONDITIONER,
)


class AgenciasWayOnline(Store):
    preferred_products_for_url_concurrency = 1
    preferred_discover_urls_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            STEREO_SYSTEM,
            REFRIGERATOR,
            AIR_CONDITIONER,
            WASHING_MACHINE,
            STOVE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ("categorias/televisores", TELEVISION),
            ("categorias/audio?marca=lg", STEREO_SYSTEM),
            ("categorias/linea-blanca/?categoria=refrigeradoras", REFRIGERATOR),
            ("categorias/linea-blanca/?categoria=lavadoras", WASHING_MACHINE),
            ("categorias/linea-blanca/?categoria=estufas", STOVE),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 15:
                    raise Exception("Page overflow")

                separator = "&" if "?" in category_path else "?"
                url = f"https://agenciasway.com.gt/{category_path}{separator}marca=lg&page={page}"
                print(url)

                soup = BeautifulSoup(session.get(url, timeout=60).text, "lxml")

                products_container = soup.find(
                    "div", {"data-widget_type": "loop-grid.product"}
                )

                if not products_container or soup.find(
                    "div", "e-loop-nothing-found-message"
                ):
                    if page == 1:
                        raise Exception("Empty path: {}".format(url))
                    break

                products = products_container.findAll("div", "product")

                for product in products:
                    product_urls.append(product.find("a")["href"])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)

        session = session_with_proxy(extra_args)
        data = session.get(url, timeout=20).text
        soup = BeautifulSoup(data, "lxml")

        key = soup.find("link", {"rel": "shortlink"})["href"].split("?p=")[-1]
        name = soup.find("h2", "product_title").text
        containers = soup.find_all("div", class_="elementor-widget-container")

        for container in containers:
            bold_tag = container.find("b")

            if bold_tag:
                text = bold_tag.text.strip().lower()
                text_value = bold_tag.next_sibling.strip()

                if text == "sku:":
                    sku = text_value
                elif text == "modelo:":
                    model = text_value

        name = f"{model} - {name}"
        price = Decimal(
            remove_words(soup.find("p", "price").find("bdi").text, blacklist=["Q", ","])
        )
        stock_tag = soup.find("span", "awl-inner-text")
        stock = 0 if stock_tag and stock_tag.text.lower() == "¡agotado!" else -1
        description_tag = soup.findAll("div", "elementor-widget-n-accordion")[1]
        picture_containers = soup.findAll("div", "woocommerce-product-gallery__image")
        picture_urls = [container.find("a")["href"] for container in picture_containers]
        description = html_to_markdown(description_tag.text)

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
            "GTQ",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=model,
        )

        return [p]
