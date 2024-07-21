import logging
from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import *

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Raenco(Store):
    @classmethod
    def categories(cls):
        return [
            REFRIGERATOR,
            AIR_CONDITIONER,
            TELEVISION,
            STEREO_SYSTEM,
            OVEN,
            WEARABLE,
            CELL,
            MONITOR,
            TABLET,
            DISH_WASHER,
            WASHING_MACHINE,
            HEADPHONES,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ["aires-acondicionados.html", AIR_CONDITIONER],
            ["audio-y-video/tv.html", TELEVISION],
            ["audio-y-video/equipos-de-sonido.html", STEREO_SYSTEM],
            ["electrodomesticos/microondas.html", OVEN],
            ["linea-blanca/refrigeradoras.html", REFRIGERATOR],
            ["linea-blanca/lavadora.html", WASHING_MACHINE],
            ["linea-blanca/secadoras.html", WASHING_MACHINE],
            ["linea-blanca/lavaplatos.html", DISH_WASHER],
            ["linea-blanca/cogeladores.html", REFRIGERATOR],
            ["tecnologia/celulares.html", CELL],
            ["tecnologia/computadoras/monitores.html", MONITOR],
            ["tecnologia/tablet.html", TABLET],
            ["tecnologia/reloj-smartwatch.html", WEARABLE],
            ["tecnologia/audifonos-y-bocinas.html", HEADPHONES],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            local_urls = []
            done = False

            while not done:
                if page >= 15:
                    raise Exception("Page overflow")

                url = "https://www.raenco.com/departamentos/{}?" "marca=221".format(
                    category_path
                )

                if page != 1:
                    url += "&p={}".format(page)

                print(url)

                res = session.get(url, timeout=60)

                if res.status_code != 200:
                    raise Exception("Invalid category: " + url)

                soup = BeautifulSoup(res.text, "lxml")
                product_containers = soup.findAll("li", "product")

                if not product_containers and page == 1:
                    logging.warning("Empty section {}".format(category_path))
                    break

                for container in product_containers:
                    product_url = container.find("a")["href"]
                    if product_url in local_urls:
                        done = True
                        break

                    local_urls.append(product_url)
                page += 1

            product_urls.extend(local_urls)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url, allow_redirects=False)

        if response.status_code in [303, 500]:
            return []

        data = response.text

        if "fatal error" in data.lower():
            return []

        soup = BeautifulSoup(data, "lxml")

        name = soup.find("h1", "page-title").text.strip()
        stock_and_sku = soup.find("div", "product-info-stock-sku")
        sku = stock_and_sku.find("div", {"itemprop": "sku"}).text.strip()
        stock_div = stock_and_sku.find("div", "stock")
        stock = int(stock_div.text.replace(stock_div.find("span").text, "").strip())

        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"]
        )

        image = soup.find("img", "gallery-placeholder__image")["src"]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            "USD",
            sku=sku,
            picture_urls=[image],
        )

        return [p]
