import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (
    HEADPHONES,
    VIDEO_GAME_CONSOLE,
    NOTEBOOK,
    KEYBOARD,
    MOUSE,
    STEREO_SYSTEM,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class Zmart(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_GAME_CONSOLE,
            MOUSE,
            KEYBOARD,
            STEREO_SYSTEM,
            NOTEBOOK,
            HEADPHONES,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = "https://www.zmart.cl"

        category_paths = [
            ["Consolas", VIDEO_GAME_CONSOLE],
            ["Asus", NOTEBOOK],
            ["logitech", KEYBOARD],
            ["Razer", MOUSE],
            [37, MOUSE],
            [38, KEYBOARD],
            [45, STEREO_SYSTEM],
            [76, HEADPHONES],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            if isinstance(category_path, int):
                page = 1

                while True:
                    if page >= 10:
                        raise Exception("Page overflow")

                    category_url = (
                        "{}/scripts/prodList.asp?sinstock=0&idCategory={}&"
                        "curPage={}".format(base_url, category_path, page)
                    )

                    soup = BeautifulSoup(session.get(category_url).text, "lxml")

                    link_containers = soup.findAll("div", "ProdBox146")

                    if not link_containers:
                        if page == 1:
                            raise Exception("Empty category: " + category_url)
                        break

                    for link_container in link_containers:
                        product_url = link_container.find("a")["href"]
                        if "http" not in product_url:
                            product_url = base_url + product_url
                        product_urls.append(product_url)
                    page += 1
            else:
                category_url = base_url + "/" + category_path

                soup = BeautifulSoup(session.get(category_url).text, "lxml")

                link_containers = soup.findAll("div", "BoxProductoS2")
                link_containers += soup.findAll("div", "ProdBox240Media")
                link_containers += soup.findAll("div", "ProdBox380_520")
                link_containers += soup.findAll("div", "BoxProductoNotebook")

                if not link_containers:
                    raise Exception("Empty category: " + category_url)

                for link_container in link_containers:
                    product_url = base_url + link_container.find("a")["href"]
                    if "idProduct" in product_url:
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
        soup = BeautifulSoup(session.get(url, verify=False).text, "lxml")

        if soup.find("div", {"id": "mensajes_sistema"}):
            return []

        name = soup.find("h1").text.strip()

        query_string = urllib.parse.urlparse(url).query
        key = urllib.parse.parse_qs(query_string)["idProduct"][0]

        if soup.find("button", {"name": "add"}):
            stock = -1
        else:
            stock = 0

        order_type_container = soup.find("div", {"id": "ficha_producto"}).find(
            "div", "txTituloRef"
        )

        if not order_type_container or "PREVENTA" in order_type_container.text:
            stock = 0

        sku = soup.find("span", "zmart__sku").text.strip()

        price_div = soup.find("div", {"id": "ficha_producto"})
        price_tags = price_div.findAll("li")

        if len(price_tags) == 0:
            return []
        elif len(price_tags) == 1:
            normal_price = Decimal(remove_words(price_tags[0].find("p").text))
            offer_price = normal_price
        elif len(price_tags) == 2:
            offer_price = Decimal(remove_words(price_tags[0].find("p").text))
            normal_price = Decimal(remove_words(price_tags[1].find("p").text))
        else:
            raise Exception("Invalid number of price tags found")

        description = html_to_markdown(
            str(soup.find("div", "tab")), "https://www.zmart.cl"
        )

        pictures_container = soup.find("ul", {"id": "imageGallery"})

        if pictures_container:
            picture_urls = []

            for tag in soup.find("ul", {"id": "imageGallery"}).findAll("li"):
                picture_path = tag["data-src"].replace(" ", "%20")
                if "http" in picture_path:
                    continue

                picture_urls.append("https://www.zmart.cl" + picture_path)
        else:
            picture_urls = None

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
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
