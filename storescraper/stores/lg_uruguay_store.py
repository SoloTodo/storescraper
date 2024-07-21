import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    TELEVISION,
    REFRIGERATOR,
    WASHING_MACHINE,
    STEREO_SYSTEM,
)
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class LgUruguayStore(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION, REFRIGERATOR, WASHING_MACHINE, STEREO_SYSTEM]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["televisores", TELEVISION],
            ["electrodomesticos/refrigeradores", REFRIGERATOR],
            ["electrodomesticos/lavado", WASHING_MACHINE],
            ["audio", STEREO_SYSTEM],
        ]
        session = session_with_proxy(extra_args)
        products_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception("page overflow: " + url_extension)
                url_webpage = (
                    "https://www.ltienda.com.uy/{}?"
                    "js=1&ord=new&pag={}".format(url_extension, page)
                )
                print(url_webpage)
                res = session.get(url_webpage)

                if res.url != url_webpage:
                    break

                data = res.text
                soup = BeautifulSoup(data, "lxml")
                product_containers = soup.find(
                    "div", {"id": "catalogoProductos"}
                ).findAll("div", "it")
                if not product_containers:
                    if page == 1:
                        logging.warning("Empty category: " + url_extension)
                    break
                for container in product_containers:
                    products_url = container.find("a")["href"]
                    products_urls.append(products_url)
                page += 1
        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("h1", "tit").text
        sku = soup.find("div", "cod").text
        if soup.find("div", "msg warn"):
            stock = 0
        else:
            stock = -1
        if soup.find("strong", "precio venta"):
            price = Decimal(
                soup.find("strong", "precio venta")
                .find("span", "monto")
                .text.replace(".", "")
            )
        else:
            return []
        if soup.find("ul", "lst lstThumbs"):
            picture_urls = [
                "https:" + tag.find("img")["src"]
                for tag in soup.find("ul", "lst lstThumbs").findAll("li")
                if tag.find("img")
            ]
        else:
            picture_urls = [
                "https:"
                + soup.find("div", {"id": "fichaProducto"})
                .find("div", "cnt")
                .find("img")["src"]
            ]
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
            picture_urls=picture_urls,
        )
        return [p]
